import os
import re
from pymongo import MongoClient
from rapidfuzz import process
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URI from .env
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["moihub_chatbot"]
collection = db["knowledge_base"]
entity_collection = db["entity_relations"]

def get_answer(question):
    """Finds the best matching question from the database using fuzzy search."""
    # First try direct question matching
    questions = [doc["question"] for doc in collection.find()]
    best_match, score, _ = process.extractOne(question, questions) if questions else (None, 0, None)

    if score > 70:
        return collection.find_one({"question": best_match})["answer"]
    
    # If no direct match, try entity-based reasoning
    # Look for questions like "Where is X?"
    location_match = re.match(r"(?i)where\s+is\s+([a-zA-Z0-9\s]+)\??", question)
    if location_match:
        entity_name = location_match.group(1).strip()
        
        # Search for statements about this entity
        entity_info = entity_collection.find_one({"entity": entity_name.lower()})
        if entity_info and "location" in entity_info:
            return entity_info["location"]
        
        # Search for statements where this entity is mentioned
        for doc in collection.find():
            if entity_name.lower() in doc["question"].lower() or entity_name.lower() in doc["answer"].lower():
                # Parse for location information
                location_info = extract_location_info(doc["question"], doc["answer"], entity_name)
                if location_info:
                    # Store this information for future use
                    entity_collection.update_one(
                        {"entity": entity_name.lower()},
                        {"$set": {"location": location_info}},
                        upsert=True
                    )
                    return location_info
    
    return None

def extract_location_info(question, answer, target_entity):
    """Extract location information about an entity from Q&A pairs."""
    # Pattern for "<Entity1> is past <Entity2>"
    past_pattern = re.search(rf"(?i)([a-zA-Z0-9\s]+)\s+is\s+past\s+([a-zA-Z0-9\s]+)", answer)
    if past_pattern:
        entity1 = past_pattern.group(1).strip()
        entity2 = past_pattern.group(2).strip()
        
        if entity1.lower() == target_entity.lower():
            return f"{entity1} is past {entity2}"
        elif entity2.lower() == target_entity.lower():
            return f"{target_entity} is before {entity1}"
    
    # Pattern for "<Entity1> is near <Entity2>"
    near_pattern = re.search(rf"(?i)([a-zA-Z0-9\s]+)\s+is\s+near\s+([a-zA-Z0-9\s]+)", answer)
    if near_pattern:
        entity1 = near_pattern.group(1).strip()
        entity2 = near_pattern.group(2).strip()
        
        if entity1.lower() == target_entity.lower():
            return f"{entity1} is near {entity2}"
        elif entity2.lower() == target_entity.lower():
            return f"{target_entity} is near {entity1}"
    
    return None

def add_knowledge(question, answer):
    """Adds new knowledge to the chatbot database and extracts entity relationships."""
    if collection.find_one({"question": question}):
        return "This question already exists!"
    
    collection.insert_one({"question": question, "answer": answer})
    
    # Extract and store entity relationships
    extract_and_store_entities(question, answer)
    
    return "Chatbot has learned a new answer!"

def extract_and_store_entities(question, answer):
    """Extract entity relationships from Q&A pairs and store them."""
    # Simple pattern for "X is past Y"
    past_pattern = re.search(r"(?i)([a-zA-Z0-9\s]+)\s+is\s+past\s+([a-zA-Z0-9\s]+)", answer)
    if past_pattern:
        entity1 = past_pattern.group(1).strip()
        entity2 = past_pattern.group(2).strip()
        
        # Store information about both entities
        entity_collection.update_one(
            {"entity": entity1.lower()},
            {"$set": {"location": f"{entity1} is past {entity2}"}},
            upsert=True
        )
        
        entity_collection.update_one(
            {"entity": entity2.lower()},
            {"$set": {"location": f"{entity2} is before {entity1}"}},
            upsert=True
        )

def get_all_knowledge():
    """Returns all knowledge items from the database."""
    knowledge_items = []
    for doc in collection.find():
        doc_dict = {k: v for k, v in doc.items() if k != '_id'}
        knowledge_items.append(doc_dict)
    return knowledge_items