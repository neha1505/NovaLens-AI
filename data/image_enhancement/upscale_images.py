import os
import sys
import argparse
import urllib.request
import cv2
import pandas as pd
import numpy as np

def download_file(url, dest_path):
    """Downloads a file from a URL to a local destination path."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    print(f"Downloading {url} to {dest_path}...")
    try:
        # Simple downloader
        urllib.request.urlretrieve(url, dest_path)
        print(f"Successfully downloaded {os.path.basename(dest_path)}.")
        return True
    except Exception as e:
        print(f"Warning: Failed to download from {url}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Upscale product images by 4x.")
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of products to upscale.')
    parser.add_argument('--all', action='store_true', help='Upscale all products in the database.')
    args = parser.parse_args()

    # Define paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    csv_path = os.path.join(base_dir, "data", "products.csv")
    data_dir = os.path.join(base_dir, "data")
    enhanced_dir = os.path.join(base_dir, "data", "enhanced_images")
    models_dir = os.path.join(base_dir, "data", "models")
    
    os.makedirs(enhanced_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    # 1. Load products database
    if not os.path.exists(csv_path):
        print(f"Error: products.csv not found at {csv_path}. Please run prepare_dataset.py first.")
        sys.exit(1)

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading products.csv: {e}")
        sys.exit(1)

    total_products = len(df)

    # Determine limit
    if args.all:
        limit = total_products
    elif args.limit is not None:
        limit = min(args.limit, total_products)
    else:
        # Safe default for testing when no arguments are supplied
        limit = min(100, total_products)
        print(f"Neither --limit nor --all was specified. Defaulting to first {limit} images for safety.")

    # Slice the database for upscaling
    process_df = df.iloc[:limit].copy()
    print(f"Found {total_products} images in database. Processing limit set to {limit}.")

    # Initialize upscalers indicators
    use_realesrgan = False
    use_opencv_sr = False
    realesrgan_model = None
    opencv_sr_model = None

    # LEVEL 1: Attempt to initialize Real-ESRGAN
    try:
        # Try importing Real-ESRGAN packages
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet
        import torch
        
        print("Checking Real-ESRGAN availability...")
        weights_path = os.path.join(models_dir, "RealESRGAN_x4plus.pth")
        
        # Download weights if not present
        if not os.path.exists(weights_path):
            realesrgan_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
            download_file(realesrgan_url, weights_path)

        if os.path.exists(weights_path):
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            # Use half precision only if GPU is active
            use_half = torch.cuda.is_available()
            
            realesrgan_model = RealESRGANer(
                scale=4,
                model_path=weights_path,
                model=model,
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=use_half,
                device=device
            )
            use_realesrgan = True
            print("Successfully initialized Real-ESRGAN.")
        else:
            print("Real-ESRGAN weights unavailable. Skipping Level 1.")
    except Exception as e:
        print(f"Real-ESRGAN is unavailable or failed to initialize: {e}")

    # LEVEL 2: Attempt to initialize OpenCV Super Resolution
    if not use_realesrgan:
        try:
            if hasattr(cv2, 'dnn_superres'):
                print("Checking OpenCV dnn_superres availability...")
                opencv_sr_model = cv2.dnn_superres.DnnSuperResImpl_create()
                # We use FSRCNN_x4 because it is extremely small (~40KB) compared to EDSR (~38MB)
                model_path = os.path.join(models_dir, "FSRCNN_x4.pb")
                
                # Download model file if not present
                if not os.path.exists(model_path):
                    fsrcnn_url = "https://github.com/Saafke/EDSR_TensorFlow/raw/master/models/FSRCNN_x4.pb"
                    download_file(fsrcnn_url, model_path)
                
                if os.path.exists(model_path):
                    opencv_sr_model.readModel(model_path)
                    opencv_sr_model.setModel("fsrcnn", 4)
                    use_opencv_sr = True
                    print("Successfully initialized OpenCV Super Resolution (FSRCNN).")
                else:
                    print("OpenCV Super Resolution model weights unavailable. Skipping Level 2.")
            else:
                print("OpenCV dnn_superres module not available in this OpenCV build.")
        except Exception as e:
            print(f"OpenCV Super Resolution failed to initialize: {e}")

    # Choose upscaling method and print it
    if use_realesrgan:
        method_desc = "Real-ESRGAN (Deep Learning)"
    elif use_opencv_sr:
        method_desc = "OpenCV Super Resolution (DNN FSRCNN)"
    else:
        method_desc = "OpenCV Lanczos4 Resampling (High-Quality Interpolation)"

    print(f"Active Upscaling Method: {method_desc}")
    print(f"Found {limit} images")

    failed_images = []
    completed_count = 0
    batch_size = 50

    # Process images in batches
    for batch_start in range(0, limit, batch_size):
        batch_end = min(batch_start + batch_size, limit)
        batch_df = process_df.iloc[batch_start:batch_end]

        for idx_in_batch, row in batch_df.iterrows():
            current_idx = completed_count + 1
            product_id = row['product_id']
            orig_image_path = row['image_path']
            
            print(f"Upscaling image {current_idx}/{limit}")

            dest_filename = f"{product_id}.jpg"
            dest_path = os.path.join(enhanced_dir, dest_filename)

            # Skip if already enhanced
            if str(orig_image_path).startswith("enhanced_images/") and os.path.exists(dest_path):
                completed_count += 1
                continue

            # Check original source path
            # Original source is either in data/fashion/images/ or from the CSV path
            src_path = os.path.join(data_dir, orig_image_path)
            # Fallback path if the product CSV path was already modified but we need the original
            fashion_src_path = os.path.join(data_dir, "fashion", "images", f"{product_id}.jpg")

            actual_src_path = None
            if os.path.exists(src_path):
                actual_src_path = src_path
            elif os.path.exists(fashion_src_path):
                actual_src_path = fashion_src_path

            if not actual_src_path:
                print(f"Warning: Source image not found for product {product_id}")
                failed_images.append((product_id, "Source image not found"))
                completed_count += 1
                continue

            try:
                # Read image
                img = cv2.imread(actual_src_path)
                if img is None:
                    raise ValueError("Failed to read image (invalid file or format)")

                h, w = img.shape[:2]
                new_h, new_w = h * 4, w * 4

                upscaled = None

                # 1. Try Real-ESRGAN
                if use_realesrgan and realesrgan_model is not None:
                    try:
                        upscaled, _ = realesrgan_model.enhance(img, outscale=4)
                    except Exception as e:
                        print(f"Real-ESRGAN enhancement failed for product {product_id}: {e}. Falling back.")

                # 2. Try OpenCV Super Resolution
                if upscaled is None and use_opencv_sr and opencv_sr_model is not None:
                    try:
                        upscaled = opencv_sr_model.upsample(img)
                    except Exception as e:
                        print(f"OpenCV Super Resolution upsample failed for product {product_id}: {e}. Falling back.")

                # 3. Fallback to Lanczos4 Interpolation
                if upscaled is None:
                    upscaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

                # Write upscaled image
                cv2.imwrite(dest_path, upscaled)

                # Update the DataFrame row in-place
                df.loc[df['product_id'] == product_id, 'image_path'] = f"enhanced_images/{dest_filename}"
                completed_count += 1

            except Exception as e:
                print(f"Error processing product {product_id}: {e}")
                failed_images.append((product_id, str(e)))
                completed_count += 1

        # Checkpoint: Save updated products.csv at the end of each batch
        try:
            df.to_csv(csv_path, index=False)
        except Exception as e:
            print(f"Warning: Error checkpointing products.csv: {e}")

    # Final print of status conforming exactly to requested output
    print(f"Completed {limit}/{limit}")

    if failed_images:
        print(f"Failed to upscale {len(failed_images)} images:")
        for pid, err in failed_images:
            print(f"  Product ID {pid}: {err}")
    else:
        print("All processed images upscaled successfully with no errors.")

if __name__ == "__main__":
    main()
