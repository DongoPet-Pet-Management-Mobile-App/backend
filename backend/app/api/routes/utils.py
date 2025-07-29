import base64
import json
import os
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests
import logging
from typing import Optional

import uuid
from app.model.pet import Pet

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic.networks import EmailStr

from langchain_openai import ChatOpenAI
from app.api.deps import get_current_active_superuser, SessionDep, CurrentUser
from app.core.prompt import Prompt
from app.models import Message, Pet
from app.utils import generate_test_email, send_email
from app.model.food_scan_result import FoodScanResult, FoodScanResultCreate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["utils"])


load_dotenv()

# Read from dotenv
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

openai_llm = ChatOpenAI(
    model=OPENAI_MODEL_NAME,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=OPENAI_API_KEY,
)

@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True

@router.post("/analyze-food-image")
async def analyze_food_image(
    session: SessionDep,
    file: UploadFile = File(...),
    pet_id: uuid.UUID = Form(...),
    include_portion_estimates: Optional[bool] = Form(False)
):
    """
    Analyze food image using OpenAI vision model and save results to database
    """
    try:
        # Verify pet exists
        pet = session.get(Pet, pet_id)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        # Read and encode image
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create enhanced system prompt
        system_prompt = Prompt.Image_Analyze_Prompt

        # Create user message
        user_text = """
            Analyze this food image with maximum precision. Identify ALL food items (including components of mixed dishes),
            provide precise nutritional values, detect reference objects, and estimate portion sizes with high accuracy. 
            Include spatial relationships between items and confidence scores for each identification.
        """

        # Generate response using OpenAI
        from langchain_core.messages import HumanMessage
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        )

        # Use the existing OpenAI client with vision capabilities
        response = openai_llm.invoke([
            ("system", system_prompt),
            message
        ])

        # Parse JSON response
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            # If response is not valid JSON, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON")

        # Ensure hasMultipleItems field exists
        if "hasMultipleItems" not in result and "foodItems" in result:
            result["hasMultipleItems"] = len(result["foodItems"]) > 1

        # Calculate nutrition health score if missing
        if "nutritionHealthScore" not in result and "foodItems" in result:
            result["nutritionHealthScore"] = _calculate_nutrition_health_score(result["foodItems"])

        # After getting the result, save to database
        if "foodItems" in result and result["foodItems"]:
            food_item = result["foodItems"][0]  # Take first item
            pet_safety = food_item.get("petSafety", {})
            health_details = result.get("healthScoreDetails", {})
            
            food_scan_create = FoodScanResultCreate(
                food_name=food_item.get("name"),
                calories=food_item.get("calories"),
                protein=food_item.get("protein"),
                carbs=food_item.get("carbs"),
                fat=food_item.get("fat"),
                fiber=food_item.get("fiber"),
                moisture=food_item.get("moisture"),
                is_safe=pet_safety.get("isSafe"),
                safety_message=pet_safety.get("safetyMessage"),
                toxic_ingredients=json.dumps(pet_safety.get("toxicIngredients", [])),
                nutrition_health_score=result.get("nutritionHealthScore"),
                health_score_description=health_details.get("description"),
                health_score_recommendations=health_details.get("recommendations"),
                has_multiple_items=result.get("hasMultipleItems", False)
            )
            
            food_scan_result = FoodScanResult.model_validate(
                food_scan_create, update={"pet_id": pet_id}
            )
            session.add(food_scan_result)
            session.commit()
            session.refresh(food_scan_result)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze food image: {str(e)}")

def _calculate_nutrition_health_score(food_items):
    """Calculate a simple nutrition health score based on food items"""
    if not food_items:
        return 50
    
    total_calories = sum(item.get("calories", 0) for item in food_items)
    total_protein = sum(item.get("protein", 0) for item in food_items)
    total_fiber = sum(item.get("fiber", 0) for item in food_items)
    total_sugar = sum(item.get("sugar", 0) for item in food_items)
    
    # Simple scoring algorithm
    score = 50  # Base score
    
    # Protein bonus
    if total_calories > 0:
        protein_ratio = (total_protein * 4) / total_calories
        score += min(protein_ratio * 100, 20)
    
    # Fiber bonus
    score += min(total_fiber * 2, 15)
    
    # Sugar penalty
    if total_calories > 0:
        sugar_ratio = (total_sugar * 4) / total_calories
        score -= min(sugar_ratio * 50, 25)
    
    return max(0, min(100, int(score)))

@router.post("/scan-barcode")
async def scan_barcode(file: UploadFile = File(...)):
    """
    Scan barcode from image and retrieve product data using OpenAI
    """
    try:
        # Read and decode image
        image_data = await file.read()
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Detect barcodes directly on color image (pyzbar works with both color and grayscale)
        barcodes = decode(image)
        
        if not barcodes:
            # Try with grayscale if color detection fails
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            barcodes = decode(gray)
            
        if not barcodes:
            raise HTTPException(
                status_code=404, 
                detail="No barcode detected in the image"
            )
        
        # Get the first barcode found
        barcode = barcodes[0]
        barcode_data = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        
        logger.info(f"Detected barcode: {barcode_data} (Type: {barcode_type})")
        
        # Create system prompt for barcode analysis
        system_prompt = """
            You are a pet food product database expert. Based on the provided barcode data and type, 
            generate comprehensive product information with detailed health analysis for pets in the exact JSON format specified below.
            
            Use your knowledge of pet food products, brands, and nutritional standards to provide 
            accurate and realistic product details. If you cannot identify the exact product, 
            provide reasonable estimates based on typical pet food products.
            
            For health analysis, evaluate the product specifically for pet safety and nutrition:
            - overall_score: 1-100 (higher is better for pets)
            - rating_label: "Excellent", "Good", "Fair", "Poor", "Bad"
            - rating_color: "#4CAF50" (good), "#FFA500" (fair), "#FF4444" (bad)
            - MUST include exactly 3 negative items and 4 positive items minimum
            - Use flexible icons that match the content (🧪🧂🍬🔥💊⚠️🧊 for negatives, 🥩🌾🍎💧🔥💪🛡️ for positives)
            - Analyze negatives: toxic ingredients, excessive sugar/sodium, harmful additives, calories, preservatives
            - Analyze positives: protein content, fiber, essential nutrients, pet-safe ingredients, vitamins, minerals
            
            Respond ONLY with valid JSON in this exact structure:
            {
                "barcode": "barcode_value",
                "barcode_type": "barcode_type",
                "product_name": "Product Name",
                "brand": "Brand Name",
                "categories": "Pet Food Category",
                "ingredients": "Detailed ingredients list",
                "serving_size": "1 cup (100g)",
                "image_url": null,
                "nutrition_grade": "B",
                "ecoscore_grade": "C",
                "nova_group": 3,
                "nutrition_facts": {
                    "energy_kcal": 350,
                    "fat": 15.0,
                    "saturated_fat": 5.0,
                    "carbohydrates": 40.0,
                    "sugars": 3.0,
                    "fiber": 4.0,
                    "proteins": 25.0,
                    "salt": 1.2,
                    "sodium": 0.5
                },
                "health_analysis": {
                    "overall_score": 85,
                    "score_max": 100,
                    "rating_label": "Good",
                    "rating_color": "#4CAF50",
                    "negatives": [
                        {
                            "icon": "🧂",
                            "title": "Sodium",
                            "subtitle": "Moderate sodium content",
                            "value": "1.2g",
                            "color": "#FFA500",
                            "details": [
                                {"label": "Daily value: 8%", "color": "#FFA500"},
                                {"label": "Recommended: <1.5g", "color": "#666"}
                            ],
                            "hasInfo": true
                        },
                        {
                            "icon": "🍬",
                            "title": "Sugar",
                            "subtitle": "Contains added sugars",
                            "value": "3g",
                            "color": "#FF4444",
                            "details": [
                                {"label": "Added sugars: 2g", "color": "#FF4444"},
                                {"label": "Natural sugars: 1g", "color": "#FFA500"}
                            ],
                            "hasInfo": true
                        },
                        {
                            "icon": "🧪",
                            "title": "Additives",
                            "subtitle": "Contains preservatives",
                            "count": 2,
                            "color": "#FFA500",
                            "details": [
                                {"label": "BHA/BHT: Present", "color": "#FFA500"},
                                {"label": "Natural preservatives: Yes", "color": "#4CAF50"}
                            ],
                            "hasInfo": true
                        }
                    ],
                    "positives": [
                        {
                            "icon": "🥩",
                            "title": "Protein",
                            "subtitle": "Excellent protein content",
                            "value": "25g",
                            "color": "#4CAF50",
                            "details": [
                                {"label": "Complete protein: 22g", "color": "#4CAF50"},
                                {"label": "Essential amino acids: Good", "color": "#4CAF50"}
                            ],
                            "hasInfo": true
                        },
                        {
                            "icon": "🌾",
                            "title": "Fiber",
                            "subtitle": "Good fiber content",
                            "value": "4g",
                            "color": "#4CAF50",
                            "details": [
                                {"label": "Supports digestion", "color": "#4CAF50"},
                                {"label": "Prebiotics included", "color": "#4CAF50"}
                            ]
                        },
                        {
                            "icon": "💧",
                            "title": "Fat Content",
                            "subtitle": "Balanced fat levels",
                            "value": "15g",
                            "color": "#4CAF50",
                            "details": [
                                {"label": "Omega-3: 2g", "color": "#4CAF50"},
                                {"label": "Omega-6: 8g", "color": "#4CAF50"}
                            ],
                            "hasInfo": true
                        },
                        {
                            "icon": "💪",
                            "title": "Vitamins",
                            "subtitle": "Essential vitamins added",
                            "value": "Complete",
                            "color": "#4CAF50",
                            "details": [
                                {"label": "Vitamin A: Good", "color": "#4CAF50"},
                                {"label": "Vitamin E: Good", "color": "#4CAF50"}
                            ]
                        }
                    ]
                }
            }
        """
        
        # Create user message with barcode data
        user_message = f"Barcode: {barcode_data}\nBarcode Type: {barcode_type}"
        
        # Generate response using OpenAI
        response = openai_llm.invoke([
            ("system", system_prompt),
            ("user", user_message)
        ])
        
        # Parse JSON response
        try:
            product_data = json.loads(response.content)
        except json.JSONDecodeError:
            # If response is not valid JSON, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                product_data = json.loads(json_match.group())
            else:
                raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON")
        
        # Debug output - log the return data
        logger.info("=== PRODUCT DATA DEBUG OUTPUT ===")
        logger.info(f"Barcode: {product_data['barcode']}")
        logger.info(f"Product Name: {product_data['product_name']}")
        logger.info(f"Brand: {product_data['brand']}")
        logger.info(f"Categories: {product_data['categories']}")
        logger.info(f"Nutrition Facts: {product_data['nutrition_facts']}")
        logger.info(f"Full Product Data: {json.dumps(product_data, indent=2)}")
        logger.info("=== END DEBUG OUTPUT ===")
        
        return {
            "success": True,
            "message": "Barcode scanned successfully",
            "data": product_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Barcode scanning failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan barcode: {str(e)}"
        )
