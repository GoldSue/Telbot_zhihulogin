import time
import random
import ddddocr
import traceback
import requests
import numpy as np
from io import BytesIO
from PIL import Image
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

print(f"[LOG] {time.strftime('%Y-%m-%d %H:%M:%S')} - 首次加载 ddddocr 滑块识别模型...")
try:
    slide = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    print(f"[LOG] {time.strftime('%Y-%m-%d %H:%M:%S')} - ddddocr 模型加载成功。")
except Exception as e:
    print(f"[LOG] 模型加载失败: {e}")
    exit()

def log(msg):
    print(f"[LOG] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def clean_background_bytes(bg_bytes, erase_width=70):
    try:
        img = Image.open(BytesIO(bg_bytes)).convert("RGB")
        np_img = np.array(img)
        avg_color = np.mean(np_img[:, -10:, :], axis=(0, 1)).astype(np.uint8)
        np_img[:, 0:erase_width, :] = avg_color
        cleaned_img = Image.fromarray(np_img)
        cleaned_img.save("bg_cleaned.png")
        output = BytesIO()
        cleaned_img.save(output, format='PNG')
        return output.getvalue()
    except Exception as e:
        log(f"❌ 背景图处理失败: {e}")
        return bg_bytes

def download_slider_from_url_with_filter(slider_element):
    src = slider_element.get_attribute("src")
    log(f"滑块图片URL: {src}")
    try:
        resp = requests.get(src)
        if resp.status_code != 200:
            return None
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
        img_np = np.array(img)
        lower = np.array([220, 220, 220])
        upper = np.array([240, 240, 240])
        r, g, b, a = img_np[:, :, 0], img_np[:, :, 1], img_np[:, :, 2], img_np[:, :, 3]
        mask = (r >= lower[0]) & (r <= upper[0]) & (g >= lower[1]) & (g <= upper[1]) & (b >= lower[2]) & (b <= upper[2])
        img_np[mask, 3] = 0
        result_img = Image.fromarray(img_np)
        result_img.save("slider_clean.png")
        output = BytesIO()
        result_img.save(output, format='PNG')
        return output.getvalue()
    except Exception as e:
        log(f"❌ 滑块图处理失败: {e}")
        return None

def get_distance(slice_bytes, bg_bytes, bg_element):
    log("调用 ddddocr 进行滑块识别...")

    # === 可调试参数 ===
    SCALE_TUNING_FACTOR = 1.1  # 手动测得的缩放因子
    # ==================

    # 动态偏移修正函数：根据识别出的距离值动态补偿
    def dynamic_bias(rough_distance):
        """
        距离动态修正函数：近时加偏移（解决偏右），远时减偏移（解决偏左）
        """
        if rough_distance <= 80:
            return -3  # 靠左时偏右，+补偿
        elif rough_distance >= 150:
            return -0  # 靠右时偏左，-补偿
        else:
            # 中间平滑过渡：线性插值
            return round(3 - 7 * (rough_distance - 80) / (150 - 80), 2)

    try:
        # 背景图预处理
        cleaned_bg = clean_background_bytes(bg_bytes)
        result = slide.slide_match(slice_bytes, cleaned_bg, simple_target=True)
        log(f"识别结果: {result}")
        target = result.get('target')
        if not target or not isinstance(target, list) or len(target) < 2:
            log("❌ 无法解析 ddddocr 返回的目标结构。")
            return -1

        x = target[0]
        if x < 5:
            log(f"❌ 检测结果过于靠左 (x={x})，放弃。")
            return -1

        # 获取缩放比例
        pixel_width = Image.open(BytesIO(cleaned_bg)).size[0]
        display_width = bg_element.size['width']
        scale_factor = (pixel_width / display_width) * SCALE_TUNING_FACTOR
        log(f"背景图缩放比: {scale_factor:.7f}")

        # 初步计算滑动距离
        rough_distance = x / scale_factor

        # 应用动态偏移修正
        bias = dynamic_bias(rough_distance)
        corrected_distance = int(rough_distance + bias)

        log(f"原始距离: {rough_distance:.2f}，动态偏移: {bias}px，最终滑动距离: {corrected_distance}")
        return corrected_distance
    except Exception as e:
        log(f"❌ ddddocr 识别出错: {e}")
        return -1

def generate_track(distance):
    def ease_out_expo(step):
        return 1 if step == 1 else 1 - pow(2, -10 * step)
    tracks = [[random.randint(20, 60), random.randint(10, 40), 0]]
    count = 30 + int(distance / 2)
    _x, _y = 0, 0
    for item in range(count):
        x = round(ease_out_expo(item / count) * distance)
        t = random.randint(10, 20)
        if x == _x:
            continue
        tracks.append([x - _x, _y, t])
        _x = x
    tracks.append([0, 0, random.randint(200, 300)])
    return tracks, sum(track[2] for track in tracks)

def try_slider(driver, bg_element, slider_element, slider_btn, max_retry=3):
    for attempt in range(1, max_retry + 1):
        log(f"➡️ 第 {attempt} 次滑动尝试")
        bg_bytes = bg_element.screenshot_as_png
        slider_bytes = download_slider_from_url_with_filter(slider_element)
        if not slider_bytes:
            log("❌ 无法获取滑块图像")
            return False

        distance = get_distance(slider_bytes, bg_bytes, bg_element)
        if distance == -1 or distance < 10:
            log(f"❌ 计算出的滑动距离异常: {distance}")
            continue

        log(f"开始滑动，目标距离: {distance}px")
        tracks, _ = generate_track(distance)
        ActionChains(driver).click_and_hold(slider_btn).perform()
        time.sleep(0.2)
        for dx, dy, dt in tracks:
            ActionChains(driver).move_by_offset(dx, dy).perform()
            time.sleep(dt / 1000)
        ActionChains(driver).release().perform()

        time.sleep(3)
        if "signin" not in driver.current_url:
            log("✅ 滑块验证通过")
            return True
        else:
            log("❌ 滑动失败，尝试重新识别")
            time.sleep(1.5)
    return False

def zhihu_slider_login_uc(username, password):
    log("启动浏览器...")
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--start-maximized')
    driver = uc.Chrome(options=options)

    try:
        log("访问知乎登录页")
        driver.get("https://www.zhihu.com/signin")
        time.sleep(2)

        log("切换至密码登录")
        driver.find_element(By.XPATH, '//div[@class="SignFlow-tabs"]/div[2]').click()
        time.sleep(1)

        driver.find_element(By.NAME, 'username').send_keys(username)
        driver.find_element(By.NAME, 'password').send_keys(password)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        time.sleep(3)

        try:
            bg_element = driver.find_element(By.CLASS_NAME, 'yidun_bgimg')
            slider_element = driver.find_element(By.CLASS_NAME, 'yidun_jigsaw')
            slider_btn = driver.find_element(By.CLASS_NAME, 'yidun_slide_indicator')
        except NoSuchElementException:
            if "signin" not in driver.current_url:
                log("✅ 登录成功，无需验证码")
                return driver.get_cookies()
            log("❌ 登录失败，页面未跳转")
            return None

        success = try_slider(driver, bg_element, slider_element, slider_btn)
        if success and "signin" not in driver.current_url:
            log("🎉 登录成功！")
            return driver.get_cookies()
        else:
            log("⚠️ 三次滑块尝试均失败")
            driver.save_screenshot("fail.png")
            return None

    except Exception as e:
        log(f"❌ 异常:\n{traceback.format_exc()}")
        return None
    finally:
        driver.quit()
        log("浏览器关闭")

if __name__ == '__main__':
    user = '17752535155'
    pwd = 'Gold7789'
    cookies = zhihu_slider_login_uc(user, pwd)
    if cookies:
        log("✅ 获取 Cookies:")
        for c in cookies:
            print(f"{c['name']} = {c['value']}")
    else:
        log("❌ 登录失败，未获取 Cookies")
