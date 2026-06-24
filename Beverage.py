# Try this code and send me output akka csv file please
"""
=============================================================
INDIA BEVERAGE DATASET GENERATOR + WEB SCRAPER
=============================================================
Generates large-scale beverage product data covering:
  - Coffee, Tea, Health Drinks, Protein Drinks
  - Women / Kids / Senior Nutrition
  - Sugar-Free, Energy, Ayurvedic Drinks
  - State-wise Sales Analysis
  - Flipkart, Amazon, BigBasket, Blinkit, JioMart scraping

COLUMNS: 25 core + 20 extra = 45 total columns

HOW TO RUN:
    pip install pandas numpy openpyxl requests beautifulsoup4 lxml fake-useragent
    python beverage_dataset.py

TO CHANGE ROWS:
    Set TOTAL_ROWS at the top of CONFIG section
"""

# =============================================================
# IMPORTS
# =============================================================
import pandas as pd
import numpy as np
import random
import os
import time
import json
import re
import requests
from datetime import datetime, timedelta

# =============================================================
# CONFIG
# =============================================================
TOTAL_ROWS   = 100_000      # Change to 1_000_000 for 10 lakh rows
CHUNK_SIZE   = 25_000       # Rows saved per CSV file
OUTPUT_DIR   = "beverage_data"
GENERATE_NOW = True          # True = generate data, False = only scrape

# =============================================================
# ALL 36 INDIA STATES & UTs  (with realistic sales weights)
# =============================================================
INDIA_STATES = {
    "Maharashtra":           0.095,
    "Uttar Pradesh":         0.090,
    "Karnataka":             0.072,
    "Tamil Nadu":            0.068,
    "Delhi":                 0.065,
    "West Bengal":           0.058,
    "Telangana":             0.052,
    "Gujarat":               0.050,
    "Rajasthan":             0.045,
    "Andhra Pradesh":        0.040,
    "Kerala":                0.038,
    "Madhya Pradesh":        0.035,
    "Punjab":                0.032,
    "Haryana":               0.028,
    "Bihar":                 0.025,
    "Odisha":                0.020,
    "Jharkhand":             0.015,
    "Assam":                 0.014,
    "Chhattisgarh":          0.013,
    "Uttarakhand":           0.012,
    "Himachal Pradesh":      0.010,
    "Goa":                   0.009,
    "Jammu and Kashmir":     0.008,
    "Chandigarh":            0.007,
    "Puducherry":            0.005,
    "Tripura":               0.004,
    "Meghalaya":             0.003,
    "Manipur":               0.003,
    "Nagaland":              0.002,
    "Arunachal Pradesh":     0.002,
    "Sikkim":                0.002,
    "Mizoram":               0.002,
    "Ladakh":                0.001,
    "Andaman and Nicobar":   0.001,
    "Dadra and Nagar Haveli":0.001,
    "Lakshadweep":           0.001,
}
STATE_NAMES   = list(INDIA_STATES.keys())
STATE_WEIGHTS = list(INDIA_STATES.values())
# normalize
_total_w = sum(STATE_WEIGHTS)
STATE_WEIGHTS = [w / _total_w for w in STATE_WEIGHTS]

# State-wise city mapping
STATE_CITIES = {
    "Maharashtra":    ["Mumbai","Pune","Nagpur","Nashik","Aurangabad","Thane","Navi Mumbai","Kolhapur","Solapur","Amravati"],
    "Uttar Pradesh":  ["Lucknow","Kanpur","Varanasi","Agra","Prayagraj","Meerut","Ghaziabad","Noida","Mathura","Bareilly"],
    "Karnataka":      ["Bengaluru","Mysuru","Hubballi","Mangaluru","Belagavi","Davangere","Shivamogga","Tumakuru","Udupi","Hassan"],
    "Tamil Nadu":     ["Chennai","Coimbatore","Madurai","Tiruchirappalli","Salem","Tirunelveli","Erode","Vellore","Tiruppur","Ooty"],
    "Delhi":          ["New Delhi","Dwarka","Rohini","Saket","Connaught Place","Karol Bagh","Lajpat Nagar","Nehru Place","Noida Ext","Janakpuri"],
    "West Bengal":    ["Kolkata","Howrah","Durgapur","Asansol","Siliguri","Bardhaman","Malda","Darjeeling","Haldia","Kharagpur"],
    "Telangana":      ["Hyderabad","Warangal","Nizamabad","Karimnagar","Khammam","Mahbubnagar","Nalgonda","Siddipet","Adilabad","Ramagundam"],
    "Gujarat":        ["Ahmedabad","Surat","Vadodara","Rajkot","Bhavnagar","Jamnagar","Gandhinagar","Anand","Morbi","Junagadh"],
    "Rajasthan":      ["Jaipur","Jodhpur","Kota","Bikaner","Ajmer","Udaipur","Bharatpur","Sikar","Alwar","Jaisalmer"],
    "Andhra Pradesh": ["Visakhapatnam","Vijayawada","Guntur","Nellore","Kurnool","Tirupati","Rajahmundry","Kakinada","Eluru","Ongole"],
    "Kerala":         ["Thiruvananthapuram","Kochi","Kozhikode","Thrissur","Kollam","Alappuzha","Kannur","Palakkad","Kottayam","Munnar"],
    "Madhya Pradesh": ["Bhopal","Indore","Gwalior","Jabalpur","Ujjain","Sagar","Dewas","Satna","Rewa","Ratlam"],
    "Punjab":         ["Ludhiana","Amritsar","Jalandhar","Patiala","Bathinda","Mohali","Pathankot","Hoshiarpur","Moga","Phagwara"],
    "Haryana":        ["Gurugram","Faridabad","Panipat","Ambala","Hisar","Rohtak","Karnal","Sonipat","Rewari","Panchkula"],
    "Bihar":          ["Patna","Gaya","Bhagalpur","Muzaffarpur","Purnia","Darbhanga","Arrah","Begusarai","Munger","Chapra"],
}
# Default cities for states not in above dict
DEFAULT_CITIES = ["State Capital","Main City","Commercial Hub","Industrial Area","Metro Area"]

# =============================================================
# PRODUCT CATALOG — Complete Beverage Universe
# =============================================================

PRODUCT_CATALOG = {
    # ── COFFEE ───────────────────────────────────────────────────────────────
    "Coffee": {
        "sub_categories": ["Instant Coffee","Filter Coffee","Cold Brew","Espresso","Cappuccino Mix","Latte Mix","Decaf Coffee","Specialty Coffee","Coffee Powder"],
        "brands": {
            "Nescafe":     {"company": "Nestle India", "premium": False},
            "Bru":         {"company": "HUL", "premium": False},
            "Continental": {"company": "Continental Coffee", "premium": True},
            "Blue Tokai":  {"company": "Blue Tokai Coffee", "premium": True},
            "Starbucks":   {"company": "Tata Starbucks", "premium": True},
            "Davidoff":    {"company": "Jacobs Douwe Egberts", "premium": True},
            "Tata Coffee": {"company": "Tata Consumer Products", "premium": False},
            "Rage Coffee": {"company": "Rage Coffee", "premium": True},
            "Seven Beans": {"company": "Seven Beans Co", "premium": True},
            "Levista":     {"company": "Levista Coffee", "premium": False},
        },
        "products": [
            ("Instant Coffee Classic",    100, 180,  220, 8.5,  6.2, 2.1),
            ("Gold Blend Premium",        200, 480,  560, 14.5, 7.8, 1.8),
            ("Filter Coffee Delight",     500, 320,  380, 12.0, 9.4, 1.5),
            ("Cold Brew Concentrate",     300, 380,  450, 10.2, 0.8, 3.2),
            ("Cappuccino Mix Sachets",    150, 220,  260, 15.5, 5.1, 8.4),
            ("Latte Powder Mix",          200, 280,  330, 13.8, 4.9, 9.2),
            ("Espresso Beans Dark",       250, 650,  780, 16.2, 8.8, 0.5),
            ("Decaf Coffee Smooth",       100, 420,  490, 14.5, 6.2, 1.2),
            ("Single Origin Arabica",     100, 550,  680, 18.5, 9.1, 0.8),
            ("Strong Brew Powder",        500, 290,  340, 11.5, 8.9, 1.8),
            ("Chicory Blend South India", 500, 260,  310, 10.8, 9.2, 2.4),
            ("French Press Coarse Grind", 200, 480,  575, 17.2, 8.4, 0.6),
        ],
        "certifications": ["FSSAI","ISO 22000","Rainforest Alliance","UTZ Certified","Organic India","Fair Trade"],
        "recommended_for": ["Working Professionals","Students","Coffee Lovers","Athletes","Senior Citizens"],
        "protein_range": (6, 14),
        "calorie_range": (5, 40),
        "sugar_range": (0.5, 12),
    },

    # ── TEA ──────────────────────────────────────────────────────────────────
    "Tea": {
        "sub_categories": ["Black Tea","Green Tea","Herbal Tea","Masala Tea","White Tea","Oolong Tea","Chai Mix","Ayurvedic Tea","Fruit Tea","Tulsi Tea"],
        "brands": {
            "Tata Tea":       {"company": "Tata Consumer Products", "premium": False},
            "Taj Mahal":      {"company": "Hindustan Unilever", "premium": True},
            "Red Label":      {"company": "Hindustan Unilever", "premium": False},
            "Lipton":         {"company": "Hindustan Unilever", "premium": False},
            "Organic India":  {"company": "Organic India Pvt Ltd", "premium": True},
            "Vahdam":         {"company": "Vahdam Teas", "premium": True},
            "Chaayos":        {"company": "Chaayos", "premium": True},
            "Wagh Bakri":     {"company": "Wagh Bakri Tea Group", "premium": False},
            "Society Tea":    {"company": "Hasmukhrai and Co", "premium": False},
            "Tetley":         {"company": "Tata Consumer Products", "premium": False},
        },
        "products": [
            ("Premium Assam Black Tea",     250, 180, 215, 0.0, 0.0, 1.2),
            ("Green Tea Natural",           100, 220, 260, 0.0, 0.0, 0.8),
            ("Masala Chai Blend",           500, 240, 285, 2.8, 0.0, 4.2),
            ("Tulsi Ginger Herbal",         100, 280, 330, 0.0, 0.0, 0.5),
            ("Chamomile Sleep Blend",       50,  320, 380, 0.0, 0.0, 0.2),
            ("Darjeeling First Flush",      100, 480, 580, 0.0, 0.0, 0.3),
            ("Immunity Kadha Mix",          200, 350, 420, 1.5, 0.0, 3.8),
            ("Lemon Ginger Green Tea",      100, 260, 310, 0.0, 0.0, 0.6),
            ("Rose Petal White Tea",        50,  420, 500, 0.0, 0.0, 0.1),
            ("Masala Chai Premix",          1000, 320, 380, 3.2, 0.0, 6.8),
            ("Elaichi Tea Bags",            200, 195, 230, 1.5, 0.0, 2.8),
            ("Organic Oolong Premium",      100, 580, 690, 0.0, 0.0, 0.4),
        ],
        "certifications": ["FSSAI","Organic India","India Organic","ISO 22000","Rainforest Alliance","PGS-India"],
        "recommended_for": ["All Age Groups","Weight Watchers","Diabetics","Senior Citizens","Pregnant Women","Fitness Enthusiasts"],
        "protein_range": (0, 2),
        "calorie_range": (0, 15),
        "sugar_range": (0, 2),
    },

    # ── HEALTH DRINKS ────────────────────────────────────────────────────────
    "Health Drinks": {
        "sub_categories": ["Malt Based","Milk Supplement","Immunity Booster","Energy Drink","Sports Drink","Electrolyte Drink","Antioxidant Drink","Vitamin Water","Probiotic Drink"],
        "brands": {
            "Horlicks":    {"company": "HUL", "premium": False},
            "Complan":     {"company": "Zydus Wellness", "premium": False},
            "Ovaltine":    {"company": "Nestle India", "premium": False},
            "Boost":       {"company": "HUL", "premium": False},
            "Bournvita":   {"company": "Mondelez India", "premium": False},
            "Pediasure":   {"company": "Abbott India", "premium": True},
            "Ensure":      {"company": "Abbott India", "premium": True},
            "Glucon-D":    {"company": "Zydus Wellness", "premium": False},
            "Enerzal":     {"company": "Elder Pharmaceuticals", "premium": False},
            "ORS":         {"company": "Mankind Pharma", "premium": False},
        },
        "products": [
            ("Malt Health Drink Chocolate", 500,  380, 445, 18.5, 14.2, 34.8),
            ("Malt Health Drink Vanilla",   500,  380, 445, 17.8, 14.2, 32.5),
            ("Kids Nutrition Powder",       1000, 720, 850, 20.5, 16.8, 38.4),
            ("Senior Care Formula",         400,  620, 730, 15.8, 12.4, 28.6),
            ("Glucose Energy Powder",       500,  180, 215, 0.0,  82.5, 320.0),
            ("Electrolyte Sports Drink",    1000, 280, 330, 0.5,  42.0, 175.0),
            ("Immunity Booster Drink Mix",  300,  480, 560, 12.5, 18.5, 95.0),
            ("Vitamin C Effervescent",      60,   320, 380, 0.0,  12.0, 48.0),
            ("Probiotic Gut Health",        200,  580, 690, 8.5,  15.0, 62.0),
            ("Multivitamin Drink Powder",   500,  540, 640, 10.5, 20.0, 88.0),
        ],
        "certifications": ["FSSAI","GMP Certified","WHO GMP","ISO 22000","Halal Certified","NABL Tested"],
        "recommended_for": ["Children","Senior Citizens","Athletes","Pregnant Women","Post Surgery","Diabetics","All Age Groups"],
        "protein_range": (8, 25),
        "calorie_range": (45, 400),
        "sugar_range": (5, 85),
    },

    # ── PROTEIN DRINKS ───────────────────────────────────────────────────────
    "Protein Drinks": {
        "sub_categories": ["Whey Protein","Plant Protein","Mass Gainer","Casein Protein","BCAA Drink","Pre-Workout","Post-Workout","Vegan Protein","Collagen Protein","Soy Protein"],
        "brands": {
            "MuscleBlaze":    {"company": "Healthkart", "premium": True},
            "Optimum Nutrition": {"company": "Glanbia", "premium": True},
            "MyProtein":      {"company": "THG Nutrition", "premium": True},
            "AS-IT-IS":       {"company": "AS-IT-IS Nutrition", "premium": False},
            "GNC":            {"company": "General Nutrition Corp", "premium": True},
            "HealthKart":     {"company": "Healthkart", "premium": False},
            "Fast&Up":        {"company": "Vitalize", "premium": True},
            "Bigmuscles":     {"company": "Bigmuscles Nutrition", "premium": False},
            "Dymatize":       {"company": "Post Holdings", "premium": True},
            "BSN":            {"company": "Glanbia Performance Nutrition", "premium": True},
        },
        "products": [
            ("Whey Protein Chocolate",      1000, 1800, 2199, 24.5, 4.2,  120.0),
            ("Whey Protein Vanilla",        2000, 3200, 3899, 25.8, 3.8,  118.0),
            ("Mass Gainer Chocolate",       3000, 2800, 3399, 30.5, 75.0, 390.0),
            ("Plant Protein Pea+Rice",      1000, 1600, 1950, 22.5, 2.5,  105.0),
            ("BCAA Powder Watermelon",      250,  1200, 1450, 7.0,  0.5,  28.0),
            ("Pre-Workout Explosive",       300,  1400, 1699, 5.5,  4.0,  45.0),
            ("Casein Protein Night",        1000, 2100, 2550, 24.0, 2.0,  108.0),
            ("Vegan Protein Combo",         500,  1500, 1799, 20.0, 3.5,  95.0),
            ("Collagen Peptides Powder",    200,  1800, 2199, 18.0, 0.0,  72.0),
            ("Soy Protein Unflavored",      1000, 1200, 1450, 27.0, 1.5,  110.0),
        ],
        "certifications": ["FSSAI","Labdoor Certified","Informed Sport","NSF Certified","Banned Substance Tested","GMP Certified"],
        "recommended_for": ["Athletes","Bodybuilders","Weight Loss","Post Workout","Vegans","Fitness Enthusiasts"],
        "protein_range": (18, 30),
        "calorie_range": (100, 420),
        "sugar_range": (0.5, 80),
    },

    # ── WOMEN'S NUTRITION ────────────────────────────────────────────────────
    "Womens Nutrition": {
        "sub_categories": ["Prenatal Nutrition","Postnatal Recovery","Bone Health","Iron Supplement","Hormonal Balance","Weight Management","Beauty Collagen","PCOS Support","Menopause Care","Calcium Drink"],
        "brands": {
            "Mamamia":       {"company": "Mamamia Foods", "premium": True},
            "Pregakem":      {"company": "Pregakem", "premium": False},
            "Horlicks Women":{"company": "HUL", "premium": False},
            "Ensure Women":  {"company": "Abbott India", "premium": True},
            "Prolyte":       {"company": "FDC Limited", "premium": False},
            "HealthFarm":    {"company": "HealthFarm Nutrition", "premium": False},
            "WOW Life":      {"company": "Body Cupid", "premium": True},
            "Nourish Vitals":{"company": "Nourish Vitals", "premium": True},
            "OZiva":         {"company": "OZiva", "premium": True},
            "Kapiva":        {"company": "Kapiva Ayurveda", "premium": True},
        },
        "products": [
            ("Prenatal Nutrition Powder",    400,  680, 799,  14.5, 15.2, 145.0),
            ("Calcium + D3 Drink Mix",       500,  580, 690,  8.5,  12.0, 88.0),
            ("Iron + Folic Acid Drink",      300,  480, 560,  6.0,  14.5, 72.0),
            ("Beauty Collagen Drink",        150,  1200, 1450, 15.0, 3.2, 62.0),
            ("PCOS Balance Herbal Drink",    200,  650, 780,  4.5,  8.0,  42.0),
            ("Postnatal Recovery Mix",       400,  720, 850,  18.5, 16.0, 165.0),
            ("Bone Strength Milk Mix",       500,  540, 640,  10.5, 18.0, 120.0),
            ("Weight Management Shake",      500,  780, 920,  20.0, 4.5,  108.0),
            ("Menopause Care Formula",       300,  880, 1050, 8.5,  6.0,  68.0),
            ("Hormonal Balance Drink",       200,  920, 1099, 5.5,  4.0,  45.0),
        ],
        "certifications": ["FSSAI","GMP Certified","Ayush Certified","ISO 22000","Organic India","Lab Tested"],
        "recommended_for": ["Pregnant Women","Lactating Mothers","Women 30+","Women with PCOS","Menopausal Women","Active Women"],
        "protein_range": (4, 22),
        "calorie_range": (40, 200),
        "sugar_range": (2, 20),
    },

    # ── KIDS NUTRITION ───────────────────────────────────────────────────────
    "Kids Nutrition": {
        "sub_categories": ["Height Growth","Brain Development","Immunity Drink","Milk Supplement","Energy Drink","Multivitamin Drink","Weight Gain","Digestive Health","Bone Builder","School Nutrition"],
        "brands": {
            "Junior Horlicks":  {"company": "HUL", "premium": False},
            "Pediasure":        {"company": "Abbott India", "premium": True},
            "Complan Growth":   {"company": "Zydus Wellness", "premium": False},
            "Gritzo":           {"company": "Gritzo", "premium": True},
            "Bournvita Little Stars": {"company": "Mondelez India", "premium": False},
            "ProteAmino Kids":  {"company": "ProteAmino", "premium": False},
            "MyProtein Kids":   {"company": "THG Nutrition", "premium": True},
            "Nestle Nangrow":   {"company": "Nestle India", "premium": True},
            "Enfagrow":         {"company": "Mead Johnson", "premium": True},
            "Similac":          {"company": "Abbott India", "premium": True},
        },
        "products": [
            ("Height Growth Chocolate",    500,  680, 799,  18.5, 22.5, 145.0),
            ("Brain Booster Vanilla",      400,  780, 920,  16.5, 18.0, 132.0),
            ("Immunity Shield Powder",     200,  580, 690,  12.5, 16.0, 112.0),
            ("DHA Enriched Milk Mix",      400,  820, 965,  15.0, 18.5, 128.0),
            ("Energy Kids Chocolate",      500,  420, 495,  14.0, 24.0, 142.0),
            ("Multivitamin Fruit Punch",   300,  480, 565,  8.5,  20.0, 88.0),
            ("Kids Weight Gain Formula",   1000, 920, 1085, 20.0, 28.0, 165.0),
            ("Digestive Probiotic Mix",    200,  640, 755,  6.5,  14.0, 72.0),
            ("Calcium Bone Builder",       500,  560, 660,  10.5, 22.0, 118.0),
            ("School Focus Brain Drink",   400,  720, 850,  14.5, 16.5, 125.0),
        ],
        "certifications": ["FSSAI","Pediatric Approved","GMP Certified","Lab Tested","ISO 22000","NABL Tested"],
        "recommended_for": ["Children 2-5 Years","Children 5-10 Years","Children 10-15 Years","Underweight Kids","Active Children"],
        "protein_range": (6, 22),
        "calorie_range": (88, 180),
        "sugar_range": (14, 30),
    },

    # ── SENIOR NUTRITION ─────────────────────────────────────────────────────
    "Senior Nutrition": {
        "sub_categories": ["Bone Health","Heart Care","Diabetic Friendly","Muscle Strength","Memory Support","Joint Care","Digestive Health","Low Sugar","High Protein Senior","Complete Nutrition"],
        "brands": {
            "Ensure Senior":  {"company": "Abbott India", "premium": True},
            "Horlicks Senior":{"company": "HUL", "premium": False},
            "Glucerna":       {"company": "Abbott India", "premium": True},
            "Protinex":       {"company": "Danone India", "premium": True},
            "Pediasure Senior":{"company": "Abbott India", "premium": True},
            "Amway Nutrilite": {"company": "Amway India", "premium": True},
            "Emvites":        {"company": "Emvites Healthcare", "premium": False},
            "Rejuven":        {"company": "Rejuven Health", "premium": False},
            "Himalaya Senior":{"company": "Himalaya Drug Company", "premium": True},
            "Dabur Senior":   {"company": "Dabur India", "premium": False},
        },
        "products": [
            ("Complete Senior Nutrition Vanilla",  400, 780, 920,  16.0, 8.5,  145.0),
            ("Diabetic Care Low Sugar",            400, 850, 1000, 14.5, 4.2,  128.0),
            ("Bone Strong Calcium Mix",            500, 680, 800,  10.5, 10.0, 112.0),
            ("Heart Healthy Oat Drink",            400, 620, 730,  8.5,  6.0,  95.0),
            ("Memory Plus Brain Nutrition",        300, 920, 1085, 12.0, 5.5,  88.0),
            ("Joint Flex Collagen Drink",          200, 1050, 1240, 15.0, 2.0, 72.0),
            ("High Protein Senior Chocolate",      400, 820, 965,  18.5, 5.5,  142.0),
            ("Muscle Strength Recovery Mix",       500, 780, 920,  20.0, 4.5,  148.0),
            ("Gut Health Probiotic Senior",        200, 680, 800,  6.5,  6.0,  65.0),
            ("Low Calorie Meal Replacement",       400, 750, 880,  22.0, 3.5,  180.0),
        ],
        "certifications": ["FSSAI","GMP Certified","Clinical Tested","ISO 22000","Diabetic Association Approved","NABL Tested"],
        "recommended_for": ["Senior Citizens 60+","Diabetic Seniors","Post Surgery","Mobility Issues","Cardiac Patients","Osteoporosis"],
        "protein_range": (8, 22),
        "calorie_range": (65, 180),
        "sugar_range": (2, 12),
    },

    # ── SUGAR-FREE PRODUCTS ──────────────────────────────────────────────────
    "Sugar Free": {
        "sub_categories": ["Zero Sugar Coffee","Sugar-Free Tea","Diabetic Drink","Keto Drink","Zero Calorie Drink","Stevia Sweetened","Low Calorie Protein","Diet Shake","Monk Fruit Sweetened","Zero Carb Drink"],
        "brands": {
            "Sugar Free":     {"company": "Zydus Wellness", "premium": False},
            "Truvia":         {"company": "Cargill", "premium": True},
            "NOW Foods":      {"company": "NOW Health Group", "premium": True},
            "Atkins":         {"company": "Atkins Nutritionals", "premium": True},
            "Keto India":     {"company": "Keto India", "premium": True},
            "Diabexy":        {"company": "Diabexy", "premium": True},
            "Lo! Foods":      {"company": "Lo! Foods", "premium": True},
            "Ketofy":         {"company": "Ketofy", "premium": True},
            "Zero Cal":       {"company": "Zero Cal India", "premium": False},
            "Diet Mug":       {"company": "Diet Mug Foods", "premium": False},
        },
        "products": [
            ("Zero Sugar Instant Coffee",    100, 380, 450,  8.5,  0.0,  8.0),
            ("Sugar Free Green Tea Mix",     100, 280, 330,  0.0,  0.0,  2.0),
            ("Keto Coffee Bulletproof",      200, 580, 690,  12.0, 0.0,  85.0),
            ("Diabetic Protein Shake",       500, 820, 965,  22.0, 0.0,  118.0),
            ("Zero Calorie Electrolyte",     300, 320, 380,  0.0,  0.0,  5.0),
            ("Stevia Tea Bags 25s",          50,  220, 260,  0.0,  0.0,  1.0),
            ("Low Carb Meal Shake Vanilla",  500, 780, 920,  20.0, 2.0,  145.0),
            ("Monk Fruit Coffee Blend",      150, 480, 565,  9.5,  0.0,  10.0),
            ("Zero Sugar Mango Punch",       500, 380, 450,  0.0,  0.0,  8.0),
            ("Keto Chocolate Shake",         400, 680, 800,  18.0, 0.5,  180.0),
        ],
        "certifications": ["FSSAI","Diabetic Friendly","Keto Certified","Zero Sugar Verified","GMP Certified","Stevia Approved"],
        "recommended_for": ["Diabetics","Keto Diet","Weight Loss","Low Carb Diet","Calorie Conscious","Pre-Diabetics"],
        "protein_range": (0, 22),
        "calorie_range": (0, 185),
        "sugar_range": (0, 3),
    },

    # ── AYURVEDIC DRINKS ─────────────────────────────────────────────────────
    "Ayurvedic Drinks": {
        "sub_categories": ["Chyawanprash Drink","Ashwagandha Milk","Brahmi Tea","Triphala Drink","Giloy Juice","Amla Juice","Neem Juice","Turmeric Latte","Moringa Drink","Shatavari Drink"],
        "brands": {
            "Patanjali":      {"company": "Patanjali Ayurved", "premium": False},
            "Dabur":          {"company": "Dabur India", "premium": False},
            "Himalaya":       {"company": "Himalaya Drug Company", "premium": True},
            "Baidyanath":     {"company": "Baidyanath Ayurved", "premium": False},
            "Kapiva":         {"company": "Kapiva Ayurveda", "premium": True},
            "Vedix":          {"company": "Vedix", "premium": True},
            "Kerala Ayurveda":{"company": "Kerala Ayurveda Ltd", "premium": True},
            "Jiva Ayurveda":  {"company": "Jiva Ayurveda", "premium": False},
            "Organic India":  {"company": "Organic India", "premium": True},
            "Sri Sri Tattva": {"company": "Sri Sri Tattva", "premium": True},
        },
        "products": [
            ("Ashwagandha Stress Relief Milk", 200, 480, 565,  8.5,  6.5,  62.0),
            ("Turmeric Golden Latte Mix",      200, 380, 450,  4.5,  8.5,  48.0),
            ("Giloy Tulsi Immunity Juice",     1000, 320, 380, 2.5,  12.0, 42.0),
            ("Amla Vitamin C Drink",           500, 280, 330,  1.5,  14.0, 58.0),
            ("Brahmi Memory Tea",              100, 350, 415,  2.0,  0.5,  12.0),
            ("Triphala Digestive Drink",       500, 420, 495,  3.5,  10.0, 45.0),
            ("Moringa Power Drink",            200, 580, 690,  6.5,  5.0,  38.0),
            ("Shatavari Women Drink",          500, 650, 765,  4.5,  12.0, 52.0),
            ("Chyawanprash Drink Mix",         500, 380, 450,  5.5,  22.0, 88.0),
            ("Neem Karela Juice Blend",        500, 250, 295,  2.0,  8.5,  35.0),
        ],
        "certifications": ["FSSAI","Ayush Certified","Organic India","India Organic","GMP Certified","ISO 22000"],
        "recommended_for": ["All Age Groups","Immunity Seekers","Stress Relief","Digestive Health","Diabetics","Senior Citizens"],
        "protein_range": (1, 9),
        "calorie_range": (12, 90),
        "sugar_range": (0.5, 24),
    },

    # ── ENERGY DRINKS ────────────────────────────────────────────────────────
    "Energy Drinks": {
        "sub_categories": ["Caffeine Based","Natural Energy","Pre-Workout Liquid","Gaming Energy","Zero Sugar Energy","Sports Energy","Vitamin Energy","Herbal Energy","Guarana Drink","B-Vitamin Boost"],
        "brands": {
            "Red Bull":       {"company": "Red Bull GmbH", "premium": True},
            "Monster":        {"company": "Monster Beverage Corp", "premium": True},
            "Sting":          {"company": "PepsiCo India", "premium": False},
            "Cloud 9":        {"company": "BM India", "premium": False},
            "Power Horse":    {"company": "Power Horse Energy", "premium": True},
            "Tzinga":         {"company": "Hector Beverages", "premium": False},
            "Charged":        {"company": "Fresca Juices", "premium": False},
            "Hell Energy":    {"company": "HELL Energy", "premium": True},
            "Rockstar":       {"company": "PepsiCo", "premium": True},
            "Burn":           {"company": "Coca-Cola India", "premium": True},
        },
        "products": [
            ("Energy Boost Original 250ml",   250, 85,  110,  0.5,  27.0, 112.0),
            ("Zero Sugar Energy Drink",        250, 95,  120,  0.0,  0.0,  10.0),
            ("Tropical Energy Blast 500ml",    500, 120, 155,  0.5,  54.0, 220.0),
            ("Natural Energy Green Tea Can",   250, 75,  95,   0.0,  8.0,  35.0),
            ("Gaming Focus Energy Drink",      330, 99,  128,  0.0,  27.0, 112.0),
            ("Sports Hydration Energy",        500, 65,  84,   0.0,  20.0, 85.0),
            ("Watermelon Vitamin Energy",      250, 89,  115,  0.0,  15.0, 62.0),
            ("Guarana Power Boost",            250, 110, 142,  0.5,  28.0, 118.0),
            ("B-Vitamin Complex Drink",        250, 95,  122,  0.0,  12.0, 50.0),
            ("Herbal Energy Ginseng",          250, 115, 148,  1.5,  10.0, 48.0),
        ],
        "certifications": ["FSSAI","FDA Approved","GMP Certified","ISO 22000","Halal Certified"],
        "recommended_for": ["Athletes","Students","Working Professionals","Gamers","Night Shift Workers"],
        "protein_range": (0, 2),
        "calorie_range": (10, 225),
        "sugar_range": (0, 55),
    },
}

# =============================================================
# MARKETPLACE CONFIGURATION
# =============================================================
MARKETPLACES = {
    "Amazon":    {"base_url": "https://www.amazon.in/s?k=", "weight": 0.35, "fee_pct": 0.12},
    "Flipkart":  {"base_url": "https://www.flipkart.com/search?q=", "weight": 0.30, "fee_pct": 0.10},
    "BigBasket": {"base_url": "https://www.bigbasket.com/ps/?q=", "weight": 0.15, "fee_pct": 0.08},
    "Blinkit":   {"base_url": "https://blinkit.com/s/?q=", "weight": 0.10, "fee_pct": 0.09},
    "JioMart":   {"base_url": "https://www.jiomart.com/search/", "weight": 0.07, "fee_pct": 0.07},
    "Meesho":    {"base_url": "https://www.meesho.com/search?q=", "weight": 0.03, "fee_pct": 0.05},
}
MKT_NAMES    = list(MARKETPLACES.keys())
MKT_WEIGHTS  = [MARKETPLACES[m]["weight"] for m in MKT_NAMES]

# Sellers per marketplace
SELLERS = {
    "Amazon":    ["Cloudtail India","Appario Retail","RetailNet","NutritionHub","HealthKart Direct","WellnessWorld","FitnessFirst","PrimeNutrition","VitaminShoppe","NutriMart"],
    "Flipkart":  ["Flipkart Grocery","RetailPath","SuperComNet","HealthDirect","WellnessKart","NutriFlip","FitZone","HealthFirst","VitaKart","NutriPlus"],
    "BigBasket": ["BigBasket Direct","BB Daily","FreshDirect","NutriBasket","HealthBasket","OrganicDirect","WholeFoods","NatureBasket","GreenBasket","PureFoods"],
    "Blinkit":   ["Blinkit Express","QuickNutri","BlinkHealth","FastFoods","SpeedNutri","BlinkDirect","QuickWellness","ZeeptoHealth","NutriBlast","HealthBlast"],
    "JioMart":   ["JioMart Fresh","JioDirect","RelianceSmart","JioHealth","JioNutri","SmartStore","RelianceDirect","JioGrocery","SmartNutri","JioWellness"],
    "Meesho":    ["MeeshoSeller1","HealthReseller","NutriReseller","FitnessReseller","WellnessReseller","DirectSeller","BestDeals","NutriDeals","HealthDeals","ValueSeller"],
}

# =============================================================
# QUALITY SCORING SYSTEM
# =============================================================
QUALITY_GRADES = {
    "A+": {"range": (90, 100), "color": "dark_green",  "description": "Premium Quality, Industry Best"},
    "A":  {"range": (80, 89),  "color": "green",       "description": "High Quality, Highly Recommended"},
    "B+": {"range": (70, 79),  "color": "light_green", "description": "Good Quality, Recommended"},
    "B":  {"range": (60, 69),  "color": "yellow",      "description": "Average Quality, Acceptable"},
    "C":  {"range": (50, 59),  "color": "orange",      "description": "Below Average, Use with Caution"},
    "D":  {"range": (0,  49),  "color": "red",         "description": "Poor Quality, Not Recommended"},
}

HEALTH_RATINGS = ["Excellent","Very Good","Good","Average","Below Average","Poor"]

# =============================================================
# HELPER FUNCTIONS
# =============================================================

def get_quality_grade(health_score):
    for grade, info in QUALITY_GRADES.items():
        lo, hi = info["range"]
        if lo <= health_score <= hi:
            return grade
    return "D"

def get_health_rating(health_score):
    if health_score >= 85:
        return "Excellent"
    elif health_score >= 70:
        return "Very Good"
    elif health_score >= 60:
        return "Good"
    elif health_score >= 50:
        return "Average"
    elif health_score >= 40:
        return "Below Average"
    else:
        return "Poor"

def compute_health_score(category, protein_g, sugar_g, calories, is_premium, certifications_count):
    # Base score from category
    base_scores = {
        "Tea": 85, "Coffee": 70, "Ayurvedic Drinks": 88,
        "Sugar Free": 82, "Senior Nutrition": 78, "Womens Nutrition": 80,
        "Kids Nutrition": 75, "Health Drinks": 72, "Protein Drinks": 76,
        "Energy Drinks": 48,
    }
    score = base_scores.get(category, 65)

    # Adjust for nutrition
    score += min(protein_g * 0.5, 10)         # protein boost max 10
    score -= min(sugar_g * 0.3, 15)            # sugar penalty max 15
    score -= min(calories * 0.015, 8)          # calorie penalty max 8
    score += certifications_count * 1.5        # cert bonus max 6
    if is_premium:
        score += 5                             # premium brand bonus

    return max(0, min(100, round(score, 1)))

def compute_profit_margin(mrp, selling_price, marketplace):
    fee_pct = MARKETPLACES.get(marketplace, {}).get("fee_pct", 0.10)
    cost_of_goods = mrp * 0.45                 # assume 45% COGS
    revenue        = selling_price
    fees           = revenue * fee_pct
    logistics      = revenue * 0.04            # 4% logistics
    net_profit     = revenue - cost_of_goods - fees - logistics
    margin         = (net_profit / revenue) * 100
    return round(max(0, margin), 2)

def make_product_id(category, index):
    cat_code = {
        "Coffee": "COF", "Tea": "TEA",
        "Health Drinks": "HLT", "Protein Drinks": "PRO",
        "Womens Nutrition": "WOM", "Kids Nutrition": "KID",
        "Senior Nutrition": "SEN", "Sugar Free": "SUG",
        "Ayurvedic Drinks": "AYU", "Energy Drinks": "ENG",
    }.get(category, "GEN")
    return f"BEV{cat_code}{index:07d}"

def make_marketplace_url(marketplace, product_name, brand):
    slug = re.sub(r"[^a-z0-9]+", "-", (brand + " " + product_name).lower()).strip("-")
    base = MARKETPLACES[marketplace]["base_url"]
    if marketplace == "Amazon":
        return f"{base}{slug.replace('-', '+')}&ref=bevdata"
    elif marketplace == "Flipkart":
        return f"{base}{slug.replace('-', '%20')}"
    elif marketplace == "BigBasket":
        return f"{base}{slug.replace('-', '%20')}&nc=true"
    elif marketplace == "Blinkit":
        return f"{base}{slug.replace('-', '%20')}"
    elif marketplace == "JioMart":
        return f"{base}{slug}"
    else:
        return f"{base}{slug}"

def get_seasonal_boost(month, category):
    seasonal = {
        "Energy Drinks":    {4: 1.3, 5: 1.4, 6: 1.5},       # Summer peak
        "Ayurvedic Drinks": {1: 1.2, 11: 1.3, 12: 1.3},     # Winter peak
        "Tea":              {11: 1.2, 12: 1.3, 1: 1.3, 2: 1.2},
        "Health Drinks":    {6: 1.1, 7: 1.1, 8: 1.1},        # Monsoon immunity
        "Kids Nutrition":   {3: 1.2, 4: 1.2},                 # School exams
    }
    return seasonal.get(category, {}).get(month, 1.0)

# =============================================================
# MAIN DATA GENERATOR
# =============================================================

def generate_chunk(chunk_idx, n, start_id):
    rng = np.random.default_rng(chunk_idx * 999 + 42)

    categories  = list(PRODUCT_CATALOG.keys())
    cat_weights = [0.12, 0.12, 0.12, 0.14, 0.10, 0.10, 0.08, 0.10, 0.08, 0.04]
    cat_arr     = rng.choice(categories, size=n, p=cat_weights)

    states_arr  = rng.choice(STATE_NAMES, size=n, p=STATE_WEIGHTS)
    mkts_arr    = rng.choice(MKT_NAMES,   size=n, p=MKT_WEIGHTS)

    order_dates = [datetime(2022,1,1) + timedelta(days=int(d)) for d in rng.integers(0, 900, size=n)]
    months_arr  = [d.month for d in order_dates]

    rows = []
    for i in range(n):
        cat       = cat_arr[i]
        cat_data  = PRODUCT_CATALOG[cat]
        state     = states_arr[i]
        mkt       = mkts_arr[i]
        month     = months_arr[i]

        # Pick brand
        brands    = list(cat_data["brands"].keys())
        brand     = random.choice(brands)
        brand_info= cat_data["brands"][brand]
        company   = brand_info["company"]
        is_premium= brand_info["premium"]

        # Pick product
        products  = cat_data["products"]
        prod      = random.choice(products)
        (prod_name, weight_g, base_mrp, base_sell,
         base_prot, base_sugar, base_cal) = prod

        sub_cat   = random.choice(cat_data["sub_categories"])

        # Price variation
        noise     = rng.uniform(0.9, 1.18)
        mrp       = round(base_mrp * noise / 5) * 5
        sell      = round(base_sell * noise / 5) * 5
        if sell > mrp:
            sell = mrp
        disc_pct  = round((mrp - sell) / mrp * 100, 1)

        # Nutrition variation
        protein   = round(base_prot + rng.uniform(-1.5, 2.5), 1)
        sugar     = round(base_sugar + rng.uniform(-2.0, 3.0), 1)
        calories  = round(base_cal  + rng.uniform(-15, 25), 1)
        protein   = max(0, protein)
        sugar     = max(0, sugar)
        calories  = max(0, calories)

        # Certifications
        all_certs = cat_data["certifications"]
        n_certs   = rng.integers(2, len(all_certs) + 1)
        certs     = "|".join(random.sample(all_certs, int(n_certs)))

        # Health score and grades
        health_score  = compute_health_score(cat, protein, sugar, calories, is_premium, int(n_certs))
        quality_grade = get_quality_grade(health_score)
        health_rating = get_health_rating(health_score)

        # Recommended for
        recommended = random.choice(cat_data["recommended_for"])

        # Rating and reviews (premium gets higher ratings)
        base_rating = rng.uniform(3.5, 5.0) if is_premium else rng.uniform(2.8, 4.8)
        rating      = round(min(5.0, base_rating), 1)

        # Reviews — popular states get more reviews
        popular_states = {"Maharashtra","Karnataka","Delhi","Tamil Nadu","Telangana","Gujarat"}
        base_reviews = 5000 if state in popular_states else 1000
        reviews      = int(rng.integers(50, base_reviews))

        # Seasonal boost on reviews
        boost        = get_seasonal_boost(month, cat)
        reviews      = int(reviews * boost)

        # Seller
        seller       = random.choice(SELLERS[mkt])

        # URL
        url          = make_marketplace_url(mkt, prod_name, brand)

        # Availability
        avail_choices = ["In Stock","In Stock","In Stock","Out of Stock","Limited Stock"]
        availability  = random.choice(avail_choices)

        # Profit margin
        profit_margin = compute_profit_margin(mrp, sell, mkt)

        # Cities
        city_list = STATE_CITIES.get(state, DEFAULT_CITIES)
        city      = random.choice(city_list)

        # Manufacturing
        mfg_states = ["Maharashtra","Karnataka","Gujarat","Uttarakhand","Himachal Pradesh",
                      "Rajasthan","Tamil Nadu","Haryana","Uttar Pradesh","Telangana"]
        mfg_state  = random.choice(mfg_states)

        # Expiry in months
        shelf_life = rng.integers(6, 36)

        # Product ID
        prod_id = make_product_id(cat, start_id + i)

        row = {
            # ── 25 CORE COLUMNS ──────────────────────────────────
            "Product_ID":            prod_id,
            "Company_Name":          company,
            "Brand_Name":            brand,
            "Category":              cat,
            "Sub_Category":          sub_cat,
            "Product_Name":          prod_name,
            "Weight_g":              weight_g,
            "MRP":                   mrp,
            "Selling_Price":         sell,
            "Discount_Percent":      disc_pct,
            "Rating":                rating,
            "Reviews":               reviews,
            "Seller_Name":           seller,
            "Marketplace":           mkt,
            "Marketplace_URL":       url,
            "Availability":          availability,
            "Protein_g":             protein,
            "Sugar_g":               sugar,
            "Calories":              calories,
            "Health_Score":          health_score,
            "Health_Rating":         health_rating,
            "Quality_Grade":         quality_grade,
            "Recommended_For":       recommended,
            "State":                 state,
            "Profit_Margin_Percent": profit_margin,
            # ── 20 EXTRA COLUMNS ─────────────────────────────────
            "City":                  city,
            "Region":                (
                "North India"     if state in ["Delhi","Haryana","Punjab","Uttar Pradesh","Uttarakhand","Himachal Pradesh","Rajasthan","Jammu and Kashmir","Ladakh","Chandigarh"]
                else "South India"     if state in ["Karnataka","Tamil Nadu","Kerala","Telangana","Andhra Pradesh","Puducherry","Lakshadweep","Andaman and Nicobar"]
                else "West India"      if state in ["Maharashtra","Gujarat","Goa","Dadra and Nagar Haveli","Daman and Diu"]
                else "East India"      if state in ["West Bengal","Odisha","Bihar","Jharkhand"]
                else "Northeast India" if state in ["Assam","Meghalaya","Manipur","Nagaland","Mizoram","Tripura","Arunachal Pradesh","Sikkim"]
                else "Central India"
            ),
            "Is_Premium_Brand":      "Yes" if is_premium else "No",
            "Certifications":        certs,
            "Certification_Count":   int(n_certs),
            "Manufacturing_State":   mfg_state,
            "Shelf_Life_Months":     int(shelf_life),
            "Order_Date":            order_dates[i].strftime("%Y-%m-%d"),
            "Order_Month":           order_dates[i].strftime("%B"),
            "Order_Quarter":         f"Q{(order_dates[i].month - 1) // 3 + 1}",
            "Order_Year":            order_dates[i].year,
            "Day_of_Week":           order_dates[i].strftime("%A"),
            "Is_Weekend_Order":      "Yes" if order_dates[i].weekday() >= 5 else "No",
            "Price_Category":        (
                "Premium (>Rs.1000)"     if sell > 1000
                else "Mid Range (500-1000)" if sell > 500
                else "Affordable (200-500)" if sell > 200
                else "Budget (<Rs.200)"
            ),
            "Fat_g":                 round(rng.uniform(0.1, 8.0), 1),
            "Carbs_g":               round(rng.uniform(2.0, 80.0), 1),
            "Sodium_mg":             round(rng.uniform(10, 450), 1),
            "Fiber_g":               round(rng.uniform(0.1, 6.0), 1),
            "Revenue_INR":           round(sell * rng.integers(1, 120), 2),
            "Units_Sold":            int(rng.integers(1, 120)),
            "Return_Rate_Percent":   round(rng.uniform(0.5, 8.0), 1),
        }
        rows.append(row)

    return pd.DataFrame(rows)


# =============================================================
# WEB SCRAPER CLASSES
# =============================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
]

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "DNT":             "1",
    })
    return s

def polite_delay(lo=2.0, hi=5.0):
    time.sleep(random.uniform(lo, hi))

def safe_get(session, url, timeout=15):
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.HTTPError as e:
        code = e.response.status_code
        if code == 429:
            print(f"    Rate limited -- sleeping 45s")
            time.sleep(45)
        elif code == 503:
            print(f"    Service unavailable -- sleeping 20s")
            time.sleep(20)
        else:
            print(f"    HTTP {code} for {url}")
    except requests.ConnectionError:
        print(f"    Connection error for {url}")
    except requests.Timeout:
        print(f"    Timeout for {url}")
    return None


class AmazonScraper:
    """
    Scrapes Amazon India beverage product listings.
    Strategies tried in order:
    1. JSON-LD structured data
    2. data-asin attribute cards
    3. s-result-item CSS selectors
    """

    SEARCH_URL = "https://www.amazon.in/s?k={query}&i=grocery&ref=bevdata"

    def __init__(self):
        self.session = make_session()

    def build_url(self, query):
        return self.SEARCH_URL.format(query=query.replace(" ", "+"))

    def scrape(self, query, state="Unknown"):
        url     = self.build_url(query)
        print(f"  [Amazon] {query}")
        resp    = safe_get(self.session, url)
        results = []

        if resp is None:
            return results

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")

        # Strategy 1: JSON-LD
        for sc in soup.find_all("script", type="application/ld+json"):
            try:
                data  = json.loads(sc.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") in ("Product","ItemList","ListItem"):
                        results.append(self._from_jsonld(item, query, state))
            except Exception:
                pass

        # Strategy 2: data-asin product cards
        if not results:
            cards = soup.select("[data-asin]")
            for card in cards:
                asin = card.get("data-asin", "")
                if not asin:
                    continue
                name_el   = card.select_one("h2 span, h2 a, [class*='title']")
                price_el  = card.select_one("[class*='price-whole'], .a-price-whole, [class*='a-price']")
                mrp_el    = card.select_one("[class*='price-was'], .a-text-strike")
                rating_el = card.select_one("[class*='a-icon-star-small'], [class*='a-star']")
                rev_el    = card.select_one("[class*='a-size-small'][href*='reviews'], [aria-label*='ratings']")

                name    = name_el.get_text(strip=True)     if name_el   else ""
                sell_p  = re.sub(r"[^\d]", "", price_el.get_text()) if price_el else "0"
                mrp_p   = re.sub(r"[^\d]", "", mrp_el.get_text())   if mrp_el   else sell_p
                rating  = re.findall(r"[\d.]+", rating_el.get("aria-label","3.5")) if rating_el else ["3.5"]
                reviews = re.sub(r"[^\d]", "", rev_el.get_text())    if rev_el   else "0"

                if name:
                    sp = int(sell_p) if sell_p else 0
                    mp = int(mrp_p)  if mrp_p  else sp
                    results.append({
                        "Product_ID":       f"AMZ{asin}",
                        "Product_Name":     name[:120],
                        "Marketplace":      "Amazon",
                        "Marketplace_URL":  f"https://www.amazon.in/dp/{asin}",
                        "Selling_Price":    sp,
                        "MRP":             mp,
                        "Discount_Percent": round((mp - sp) / mp * 100, 1) if mp > 0 else 0,
                        "Rating":           float(rating[0]) if rating else 3.5,
                        "Reviews":          int(reviews) if reviews else 0,
                        "State":            state,
                        "Category":         self._guess_category(query),
                        "Availability":     "In Stock",
                    })

        # Strategy 3: generic result items
        if not results:
            for card in soup.select(".s-result-item[data-component-type='s-search-result']"):
                name_el   = card.select_one("h2")
                price_el  = card.select_one(".a-price-whole")
                if name_el and price_el:
                    name  = name_el.get_text(strip=True)
                    price = re.sub(r"[^\d]", "", price_el.get_text())
                    results.append({
                        "Product_Name": name[:120],
                        "Marketplace":  "Amazon",
                        "Selling_Price": int(price) if price else 0,
                        "State":        state,
                        "Category":     self._guess_category(query),
                    })

        polite_delay()
        print(f"    Found {len(results)} products")
        return results

    def _from_jsonld(self, item, query, state):
        offers = item.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        return {
            "Product_ID":      "",
            "Product_Name":    item.get("name", "")[:120],
            "Brand_Name":      item.get("brand", {}).get("name", "") if isinstance(item.get("brand"), dict) else "",
            "Marketplace":     "Amazon",
            "Marketplace_URL": item.get("url", ""),
            "Selling_Price":   float(str(offers.get("price", 0)).replace(",","")),
            "MRP":             float(str(offers.get("price", 0)).replace(",","")),
            "Discount_Percent":0,
            "Rating":          float(item.get("aggregateRating", {}).get("ratingValue", 0) or 0),
            "Reviews":         int(item.get("aggregateRating", {}).get("reviewCount", 0) or 0),
            "Availability":    "In Stock",
            "State":           state,
            "Category":        self._guess_category(query),
        }

    def _guess_category(self, query):
        q = query.lower()
        if "coffee"  in q: return "Coffee"
        if "tea"     in q: return "Tea"
        if "protein" in q: return "Protein Drinks"
        if "energy"  in q: return "Energy Drinks"
        if "kids"    in q: return "Kids Nutrition"
        if "senior"  in q: return "Senior Nutrition"
        if "women"   in q: return "Womens Nutrition"
        if "sugar free" in q or "keto" in q: return "Sugar Free"
        if "ayurved" in q or "herbal" in q: return "Ayurvedic Drinks"
        return "Health Drinks"


class FlipkartScraper:
    """
    Scrapes Flipkart beverage product listings.
    Strategies: JSON-LD -> _product divs -> script JSON blobs
    """
    SEARCH_URL = "https://www.flipkart.com/search?q={query}&otracker=search&marketplace=FLIPKART"

    def __init__(self):
        self.session = make_session()
        # Flipkart requires these headers
        self.session.headers.update({
            "Referer":       "https://www.flipkart.com",
            "X-User-Agent":  "Mozilla/5.0 (compatible; BeverageBot/1.0)",
        })

    def build_url(self, query):
        return self.SEARCH_URL.format(query=query.replace(" ", "%20"))

    def scrape(self, query, state="Unknown"):
        url  = self.build_url(query)
        print(f"  [Flipkart] {query}")
        resp = safe_get(self.session, url)
        if resp is None:
            return []

        from bs4 import BeautifulSoup
        soup    = BeautifulSoup(resp.text, "lxml")
        results = []

        # Strategy 1: JSON-LD
        for sc in soup.find_all("script", type="application/ld+json"):
            try:
                data  = json.loads(sc.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") == "Product":
                        offers = item.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        results.append({
                            "Product_ID":      "",
                            "Product_Name":    item.get("name", "")[:120],
                            "Brand_Name":      item.get("brand", {}).get("name", "") if isinstance(item.get("brand"), dict) else "",
                            "Marketplace":     "Flipkart",
                            "Marketplace_URL": item.get("url", url),
                            "Selling_Price":   float(str(offers.get("price","0")).replace(",","")),
                            "MRP":             float(str(offers.get("price","0")).replace(",","")),
                            "Discount_Percent":0,
                            "Rating":          float(item.get("aggregateRating",{}).get("ratingValue",0) or 0),
                            "Reviews":         int(item.get("aggregateRating",{}).get("reviewCount",0) or 0),
                            "Availability":    "In Stock",
                            "State":           state,
                            "Category":        self._guess_cat(query),
                        })
            except Exception:
                pass

        # Strategy 2: Flipkart product tiles
        if not results:
            # Flipkart uses _1AtVbE or similar class names (they rotate them)
            card_sels = [
                "div[data-id]",
                "div._1AtVbE",
                "div._2kHMtA",
                "._4ddWXP",
                "div.s1Q9rs",
                "[class*='productBase']",
                "div._13oc-S",
            ]
            cards = []
            for sel in card_sels:
                cards = soup.select(sel)
                if len(cards) > 2:
                    break

            for card in cards:
                name_el   = card.select_one("div._4rR01T, a.s1Q9rs, ._3wU53n, [class*='title']")
                price_el  = card.select_one("div._30jeq3, ._1_WHN1, [class*='price']")
                mrp_el    = card.select_one("div._3I9_wc, ._27UcVY, [class*='strike']")
                disc_el   = card.select_one("div._3Ay6Sb, [class*='discount']")
                rating_el = card.select_one("div._3LWZlK, [class*='rating']")
                rev_el    = card.select_one("span._2_R_DZ, [class*='count']")
                link_el   = card.find("a", href=True)

                name    = name_el.get_text(strip=True)     if name_el   else ""
                sell_s  = re.sub(r"[^\d]", "", price_el.get_text()) if price_el else "0"
                mrp_s   = re.sub(r"[^\d]", "", mrp_el.get_text())   if mrp_el   else sell_s
                disc_s  = re.sub(r"[^\d]", "", disc_el.get_text())  if disc_el  else "0"
                rat_s   = re.sub(r"[^\d.]", "", rating_el.get_text()) if rating_el else "3.5"
                rev_s   = re.sub(r"[^\d]", "", rev_el.get_text())   if rev_el   else "0"
                href    = link_el["href"] if link_el else ""
                full_url= f"https://www.flipkart.com{href}" if href.startswith("/") else href

                if name:
                    sp = int(sell_s) if sell_s else 0
                    mp = int(mrp_s)  if mrp_s  else sp
                    results.append({
                        "Product_Name":    name[:120],
                        "Marketplace":     "Flipkart",
                        "Marketplace_URL": full_url,
                        "Selling_Price":   sp,
                        "MRP":             mp,
                        "Discount_Percent":int(disc_s) if disc_s else round((mp-sp)/mp*100,1) if mp>0 else 0,
                        "Rating":          float(rat_s) if rat_s else 3.5,
                        "Reviews":         int(rev_s) if rev_s else 0,
                        "Availability":    "In Stock",
                        "State":           state,
                        "Category":        self._guess_cat(query),
                    })

        polite_delay()
        print(f"    Found {len(results)} products")
        return results

    def _guess_cat(self, query):
        q = query.lower()
        if "coffee"  in q: return "Coffee"
        if "tea"     in q: return "Tea"
        if "protein" in q: return "Protein Drinks"
        if "energy"  in q: return "Energy Drinks"
        if "kids"    in q: return "Kids Nutrition"
        if "senior"  in q: return "Senior Nutrition"
        if "women"   in q: return "Womens Nutrition"
        if "keto" in q or "sugar free" in q: return "Sugar Free"
        if "ayurved" in q: return "Ayurvedic Drinks"
        return "Health Drinks"


class BigBasketScraper:
    """
    Scrapes BigBasket product listings.
    """
    SEARCH_URL = "https://www.bigbasket.com/ps/?q={query}&nc=true"

    def __init__(self):
        self.session = make_session()
        self.session.headers.update({"Referer": "https://www.bigbasket.com"})

    def scrape(self, query, state="Unknown"):
        url  = self.SEARCH_URL.format(query=query.replace(" ", "%20"))
        print(f"  [BigBasket] {query}")
        resp = safe_get(self.session, url)
        if resp is None:
            return []

        from bs4 import BeautifulSoup
        soup    = BeautifulSoup(resp.text, "lxml")
        results = []

        # BigBasket JSON in script tags
        for sc in soup.find_all("script"):
            text = sc.string or ""
            if "productCategory" in text or "selling_price" in text:
                try:
                    matches = re.findall(r'\{[^{}]{100,}\}', text)
                    for m in matches[:20]:
                        try:
                            d = json.loads(m)
                            name = d.get("desc") or d.get("name") or d.get("product_name", "")
                            if name:
                                results.append({
                                    "Product_Name":    str(name)[:120],
                                    "Marketplace":     "BigBasket",
                                    "Marketplace_URL": f"https://www.bigbasket.com/pd/{d.get('id','')}/",
                                    "Selling_Price":   float(d.get("sp", d.get("selling_price", 0)) or 0),
                                    "MRP":             float(d.get("mrp", 0) or 0),
                                    "Rating":          float(d.get("rating", 3.5) or 3.5),
                                    "Reviews":         int(d.get("ratingCount", 0) or 0),
                                    "State":           state,
                                    "Category":        self._guess_cat(query),
                                    "Availability":    "In Stock",
                                })
                        except Exception:
                            pass
                except Exception:
                    pass

        # HTML fallback
        if not results:
            cards = soup.select("[class*='product'], [class*='item'], li[id*='product']")
            for card in cards[:30]:
                name_el  = card.select_one("[class*='prod-name'], h4, h3, [class*='name']")
                price_el = card.select_one("[class*='sp'], [class*='price'], [class*='discnt-price']")
                mrp_el   = card.select_one("[class*='mrp'], [class*='strike'], strike")
                if name_el:
                    sell_s = re.sub(r"[^\d]", "", price_el.get_text()) if price_el else "0"
                    mrp_s  = re.sub(r"[^\d]", "", mrp_el.get_text())   if mrp_el   else sell_s
                    sp     = int(sell_s) if sell_s else 0
                    mp     = int(mrp_s)  if mrp_s  else sp
                    results.append({
                        "Product_Name":    name_el.get_text(strip=True)[:120],
                        "Marketplace":     "BigBasket",
                        "Marketplace_URL": url,
                        "Selling_Price":   sp,
                        "MRP":             mp,
                        "Discount_Percent": round((mp-sp)/mp*100,1) if mp > 0 else 0,
                        "Rating":          0,
                        "Reviews":         0,
                        "State":           state,
                        "Category":        self._guess_cat(query),
                        "Availability":    "In Stock",
                    })

        polite_delay()
        print(f"    Found {len(results)} products")
        return results

    def _guess_cat(self, query):
        q = query.lower()
        if "coffee" in q: return "Coffee"
        if "tea"    in q: return "Tea"
        if "protein"in q: return "Protein Drinks"
        if "energy" in q: return "Energy Drinks"
        if "kids"   in q: return "Kids Nutrition"
        if "ayurved"in q: return "Ayurvedic Drinks"
        return "Health Drinks"


def run_scrapers(queries=None, states_to_scrape=None):
    """
    Run all scrapers for given queries and states.
    queries: list of search strings
    states_to_scrape: list of state names (for labeling data)
    """
    if queries is None:
        queries = [
            "instant coffee",    "green tea bags",
            "protein powder",    "health drink malt",
            "kids nutrition",    "senior nutrition ensure",
            "women nutrition",   "sugar free coffee",
            "ayurvedic drink",   "energy drink india",
        ]
    if states_to_scrape is None:
        states_to_scrape = ["Maharashtra","Karnataka","Delhi","Tamil Nadu","West Bengal"]

    amazon_s    = AmazonScraper()
    flipkart_s  = FlipkartScraper()
    bigbasket_s = BigBasketScraper()

    all_results = []
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for query in queries:
        for state in states_to_scrape[:2]:    # limit to 2 states per query in demo
            print(f"\nQuery: '{query}' | State: {state}")

            rows = amazon_s.scrape(query, state)
            all_results.extend(rows)

            rows = flipkart_s.scrape(query, state)
            all_results.extend(rows)

            rows = bigbasket_s.scrape(query, state)
            all_results.extend(rows)

    if all_results:
        df = pd.DataFrame(all_results)
        out = f"{OUTPUT_DIR}/scraped_beverages.csv"
        df.to_csv(out, index=False)
        kb = os.path.getsize(out) / 1024
        print(f"\nScraped data saved: {out} | {len(df)} rows | {kb:,.0f} KB")
    else:
        print("\nNo scraped data (sites may require browser rendering).")

    return all_results


# =============================================================
# MAIN
# =============================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    t0 = time.time()

    print("=" * 65)
    print("  INDIA BEVERAGE DATASET GENERATOR")
    print(f"  Total rows : {TOTAL_ROWS:,}")
    print(f"  Chunk size : {CHUNK_SIZE:,}")
    print(f"  Output     : {OUTPUT_DIR}/")
    print("=" * 65)

    if GENERATE_NOW:
        n_chunks      = TOTAL_ROWS // CHUNK_SIZE
        total_written = 0
        file_sizes    = []

        for ci in range(n_chunks):
            print(f"\n  Chunk {ci+1}/{n_chunks}  ({CHUNK_SIZE:,} rows)...")
            df = generate_chunk(ci, CHUNK_SIZE, total_written)

            fname = f"{OUTPUT_DIR}/beverages_chunk_{ci+1:03d}.csv"
            df.to_csv(fname, index=False)

            kb = os.path.getsize(fname) / 1024
            file_sizes.append({
                "Chunk":    ci + 1,
                "Filename": fname,
                "Rows":     len(df),
                "Size_KB":  round(kb, 2),
                "Size_MB":  round(kb / 1024, 3),
            })
            total_written += len(df)
            print(f"  Written: {total_written:,} rows | {kb:,.0f} KB")

        # Save size summary
        sz_df = pd.DataFrame(file_sizes)
        sz_path = f"{OUTPUT_DIR}/00_SIZE_SUMMARY.csv"
        sz_df.to_csv(sz_path, index=False)

        elapsed = time.time() - t0
        total_kb = sum(f["Size_KB"] for f in file_sizes)

        print("\n" + "=" * 65)
        print("  DONE!")
        print(f"  Total rows  : {total_written:,}")
        print(f"  Total files : {n_chunks}")
        print(f"  Total size  : {total_kb:,.0f} KB  |  {total_kb/1024:.1f} MB")
        print(f"  Time taken  : {elapsed:.0f} seconds")
        print("=" * 65)
        print("\n  COLUMNS (45 total):")
        sample = pd.read_csv(f"{OUTPUT_DIR}/beverages_chunk_001.csv", nrows=0)
        for i, col in enumerate(sample.columns, 1):
            print(f"   {i:2d}. {col}")

    else:
        print("\n  Running web scrapers...")
        run_scrapers()

    print("\n  To change rows: set TOTAL_ROWS at the top of the file.")
    print("  To run real scraping: set GENERATE_NOW = False")


if __name__ == "__main__":
    main()


# ============================================================
#  INDIA E-COMMERCE FASHION SCRAPER — Google Colab Version
#  Platforms : Myntra · Amazon India · Flipkart · Ajio
#  Output    : CSV  +  Excel Analytics Workbook
#  28 Columns | Works in Jupyter / Google Colab
# ============================================================

# ── STEP 1 : Install dependencies ────────────────────────────
import subprocess, sys

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

for pkg in ["requests", "beautifulsoup4", "pandas", "openpyxl",
            "fake-useragent", "lxml", "tqdm"]:
    install(pkg)

print("✅ All packages installed")

# ── STEP 2 : CONFIG — change these as needed ─────────────────
CONFIG = {
    # Which platforms to scrape: "all" or list like ["myntra","amazon"]
    "platforms": "all",

    # Max pages per category (more pages = more products)
    "max_pages": 4,

    # Delay between requests in seconds (min, max)
    "delay_min": 1.5,
    "delay_max": 3.5,

    # Optional proxy list. Leave empty [] for direct connection.
    # Format: "http://user:pass@host:port"
    "proxies": [],

    # Output folder (Colab: use /content/)
    "output_dir": "/content/scraped_data",

    # Retry attempts on failure
    "max_retries": 3,
}

# ─────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────
import os, re, csv, time, random, logging, json
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm.notebook import tqdm   # notebook-friendly progress bar

try:
    from fake_useragent import UserAgent
    _ua = UserAgent()
    def random_ua(): return _ua.random
except Exception:
    _AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    ]
    def random_ua(): return random.choice(_AGENTS)

# ─────────────────────────────────────────────────────────────
# SETUP PATHS & LOGGING
# ─────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(CONFIG["output_dir"])
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP  = datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_OUT    = OUTPUT_DIR / f"india_fashion_{TIMESTAMP}.csv"
EXCEL_OUT  = OUTPUT_DIR / f"india_fashion_analytics_{TIMESTAMP}.xlsx"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(OUTPUT_DIR / "scraper.log"), encoding="utf-8"),
    ],
)
log = logging.getLogger("EcomScraper")
log.info(f"Output directory: {OUTPUT_DIR}")