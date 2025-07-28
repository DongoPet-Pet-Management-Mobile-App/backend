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
    current_user: CurrentUser,
    file: UploadFile = File(...),
    pet_id: uuid.UUID = Form(...),
    include_portion_estimates: Optional[bool] = Form(False)
):
    """
    Analyze food image using OpenAI vision model and save results to database
    """
    try:
        # Verify pet ownership
        pet = session.get(Pet, pet_id)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        if pet.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Not enough permissions")
        
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
    Scan barcode from image and retrieve product data from Open Food Facts API
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
        
        # Get product data from Open Food Facts API
        api_url = f"https://world.openpetfoodfacts.org/api/v0/product/{barcode_data}.json"

        response = requests.get(api_url, timeout=10)

        print("Barcode API response: ", response.content)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch product data from API: {response.status_code}"
            )
        
        api_data = response.json()
        
        if api_data.get("status") != 1:
            raise HTTPException(
                status_code=404,
                detail=f"Product not found for barcode: {barcode_data}"
            )
        
        product = api_data.get("product", {})
        
        # Extract relevant product information
        product_data = {
            "barcode": barcode_data,
            "barcode_type": barcode_type,
            "product_name": product.get("product_name", "Unknown"),
            "brand": product.get("brands", "Unknown"),
            "categories": product.get("categories", "Unknown"),
            "ingredients": product.get("ingredients_text", "Not available"),
            "nutrition_facts": {
                "energy_kcal": product.get("nutriments", {}).get("energy-kcal_100g"),
                "fat": product.get("nutriments", {}).get("fat_100g"),
                "saturated_fat": product.get("nutriments", {}).get("saturated-fat_100g"),
                "carbohydrates": product.get("nutriments", {}).get("carbohydrates_100g"),
                "sugars": product.get("nutriments", {}).get("sugars_100g"),
                "fiber": product.get("nutriments", {}).get("fiber_100g"),
                "proteins": product.get("nutriments", {}).get("proteins_100g"),
                "salt": product.get("nutriments", {}).get("salt_100g"),
                "sodium": product.get("nutriments", {}).get("sodium_100g")
            },
            "serving_size": product.get("serving_size"),
            "packaging": product.get("packaging"),
            "labels": product.get("labels"),
            "image_url": product.get("image_url"),
            "nutrition_grade": product.get("nutrition_grades"),
            "ecoscore_grade": product.get("ecoscore_grade"),
            "nova_group": product.get("nova_group")
        }
        
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
    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch product data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Barcode scanning failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan barcode: {str(e)}"
        )

