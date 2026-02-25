from PIL import Image
import os

def remove_white_background(input_path, output_path, tolerance=200):
    print(f"Processing {input_path}...")
    try:
        img = Image.open(input_path)
        img = img.convert("RGBA")
        
        datas = img.getdata()
        
        new_data = []
        for item in datas:
            # Check if pixel is close to white
            if item[0] > tolerance and item[1] > tolerance and item[2] > tolerance:
                new_data.append((255, 255, 255, 0)) # Transparent
            else:
                new_data.append(item)
        
        img.putdata(new_data)
        img.save(output_path, "PNG")
        print(f"Saved to {output_path}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

base_dir = "c:/Users/geevi/Downloads/Smart_Lab_Report_Analyser/frontend/assets/images"
input_watching = os.path.join(base_dir, "new_doctor_watching.png")
input_hiding = os.path.join(base_dir, "new_doctor_hiding.png")

output_watching = os.path.join(base_dir, "transparent_doctor_watching.png")
output_hiding = os.path.join(base_dir, "transparent_doctor_hiding.png")

remove_white_background(input_watching, output_watching)
remove_white_background(input_hiding, output_hiding)
