from PIL import Image

slider_raw_img = Image.open("slider.png")
width, height = slider_raw_img.size
print(f"原始图尺寸: {width}x{height}")

# 如果你观察得出滑块图案位于靠下部分，可以手动裁剪
# 例如从 y=160 高度开始裁剪 60×60
crop_x, crop_y = 2, 10
crop_w, crop_h = 60, 60
slider_crop = slider_raw_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
open("slider_crop.png", "wb").write(slider_crop.tobytes())

