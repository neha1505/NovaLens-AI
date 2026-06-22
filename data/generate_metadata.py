import os
import csv
import hashlib
import random

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
deepfashion_dir = os.path.join(base_dir, "data", "DeepFashion")
img_highres_dir = os.path.join(deepfashion_dir, "img_highres")
output_dir = os.path.join(base_dir, "data", "processed")
output_csv = os.path.join(output_dir, "products.csv")

# Predefined dictionaries for name generation
adjectives = ['Classic', 'Premium', 'Essential', 'Modern', 'Vintage', 'Casual', 'Stylish', 'Comfort', 'Soft-Knit', 'Slim-Fit', 'Relaxed-Fit', 'Designer', 'Sporty', 'Urban', 'Elegant', 'Cozy']
colors = ['Black', 'White', 'Charcoal', 'Navy Blue', 'Olive Green', 'Burgundy', 'Mustard', 'Beige', 'Crimson Red', 'Indigo', 'Heather Grey', 'Pastel Pink', 'Teal', 'Cream', 'Khaki', 'Rust']

base_names = {
    'Denim': ['Jeans', 'Denim Jacket', 'Denim Shorts', 'Denim Shirt'],
    'Jackets_Vests': ['Utility Jacket', 'Lightweight Vest', 'Windbreaker', 'Bomber Jacket'],
    'Pants': ['Chino Pants', 'Casual Trousers', 'Slim Fit Pants', 'Cargo Pants'],
    'Shirts_Polos': ['Polo Shirt', 'Classic Button-Down Shirt', 'Oxford Shirt', 'Casual Linen Shirt'],
    'Shorts': ['Cotton Shorts', 'Casual Chino Shorts', 'Active Shorts'],
    'Suiting': ['Slim Fit Blazer', 'Suit Jacket', 'Tailored Blazer'],
    'Sweaters': ['Crewneck Sweater', 'V-Neck Pullover', 'Cable Knit Sweater'],
    'Sweatshirts_Hoodies': ['Fleece Hoodie', 'Pullover Sweatshirt', 'Zip-Up Hoodie'],
    'Tees_Tanks': ['Crewneck Tee', 'Athletic Tank Top', 'V-Neck Tee'],
    'Blouses_Shirts': ['Elegant Blouse', 'Casual Blouse', 'Silk Shirt', 'Lace Top'],
    'Cardigans': ['Soft Knit Cardigan', 'Open-Front Cardigan', 'Longline Cardigan'],
    'Dresses': ['Floral A-Line Dress', 'Classic Party Dress', 'Maxi Dress', 'Cocktail Dress'],
    'Graphic_Tees': ['Printed Graphic Tee', 'Vintage Graphic Tee', 'Retro Logo Tee'],
    'Jackets_Coats': ['Warm Trench Coat', 'Winter Coat', 'Classic Jacket', 'Parka'],
    'Leggings': ['High-Waisted Leggings', 'Stretch Yoga Pants', 'Athletic Leggings'],
    'Rompers_Jumpsuits': ['Summer Romper', 'Elegant Jumpsuit', 'Casual Romper'],
    'Skirts': ['Flowy Pleated Skirt', 'Denim Skirt', 'Classic Pencil Skirt']
}

materials = ['cotton blend', 'premium polyester', 'soft knit fabric', 'high-quality denim', 'fleece fabric', 'linen blend', 'pure wool', 'silk blend']
fits = ['relaxed fit', 'slim fit', 'regular fit', 'classic fit', 'modern fit', 'oversized fit']
occasions = ['casual everyday wear', 'formal gatherings', 'outdoor activities', 'weekend lounging', 'special occasions', 'athletic workouts']

def get_seeded_random(product_id: str):
    seed = int(hashlib.md5(product_id.encode('utf-8')).hexdigest(), 16) % (10**8)
    return random.Random(seed)

def generate_metadata():
    print("=== Generating NovaLens Compatible Metadata ===")
    if not os.path.exists(img_highres_dir):
        print(f"Error: img_highres directory not found at {img_highres_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)
    products = []
    genders = ["MEN", "WOMEN"]

    for gender in genders:
        gender_dir = os.path.join(img_highres_dir, gender)
        if not os.path.exists(gender_dir):
            continue
        
        categories = os.listdir(gender_dir)
        for category in categories:
            cat_dir = os.path.join(gender_dir, category)
            if not os.path.isdir(cat_dir):
                continue
            
            product_folders = os.listdir(cat_dir)
            for prod_folder in product_folders:
                prod_dir = os.path.join(cat_dir, prod_folder)
                if not os.path.isdir(prod_dir) or not prod_folder.startswith("id_"):
                    continue
                
                # Globally unique product ID
                product_id = f"{gender}_{category}_{prod_folder}"
                
                # List files and find primary image
                files = os.listdir(prod_dir)
                jpg_files = [f for f in files if f.endswith(".jpg")]
                if not jpg_files:
                    continue
                
                # Priority: 1_front.jpg -> 4_full.jpg -> 6_flat.jpg -> first jpg
                primary_image = None
                for suffix in ["1_front.jpg", "4_full.jpg", "6_flat.jpg"]:
                    for f in jpg_files:
                        if f.endswith(suffix):
                            primary_image = f
                            break
                    if primary_image:
                        break
                
                if not primary_image:
                    primary_image = jpg_files[0]
                
                # Relative primary image path
                primary_image_path = f"DeepFashion/img_highres/{gender}/{category}/{prod_folder}/{primary_image}"
                
                # All image paths (JPEGs + PNGs) relative to data/
                all_images = [f"DeepFashion/img_highres/{gender}/{category}/{prod_folder}/{f}" for f in files if f.endswith((".jpg", ".png"))]
                all_image_paths_str = ";".join(all_images)
                
                # Seeded random generator
                r = get_seeded_random(product_id)
                
                # Generate Name
                adj = r.choice(adjectives)
                color = r.choice(colors)
                base_list = base_names.get(category, ['Apparel Item'])
                base_name = r.choice(base_list)
                
                # Avoid duplicates in category name
                product_name = f"{gender.capitalize()}'s {adj} {color} {base_name}"
                
                # Generate Description
                material = r.choice(materials)
                fit = r.choice(fits)
                occ = r.choice(occasions)
                description = f"A stylish {product_name.lower()} featuring a comfortable {fit} and made from a durable {material}. Ideal for {occ}."
                
                # Generate Price (INR)
                price = float(r.randint(499, 4999))
                
                products.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "category": category,
                    "description": description,
                    "price": price,
                    "primary_image": primary_image_path,
                    "all_image_paths": all_image_paths_str
                })

    print(f"Total processed products: {len(products)}")
    
    # Save to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["product_id", "product_name", "category", "description", "price", "primary_image", "all_image_paths"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)
        
    print(f"Saved product catalog to: {output_csv}")

if __name__ == "__main__":
    generate_metadata()
