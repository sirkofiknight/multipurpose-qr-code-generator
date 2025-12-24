import gradio as gr
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer,
    CircleModuleDrawer,
    GappedSquareModuleDrawer,
    SquareModuleDrawer
)
from qrcode.image.styles.colormasks import SolidFillColorMask, SquareGradiantColorMask
from PIL import Image, ImageOps, ImageDraw, ImageFont
import io
import base64
import json
import csv
import os
from datetime import datetime
import requests
from urllib.parse import urlparse
import re


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_app():
    """Initialize application and create necessary files"""
    # Create output directory if it doesn't exist
    output_dir = "/mnt/user-data/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create history file if it doesn't exist
    history_file = os.path.join(output_dir, 'qr_history.json')
    
    if not os.path.exists(history_file):
        try:
            with open(history_file, 'w') as f:
                json.dump([], f)
        except Exception:
            pass  # Fail silently


# =============================================================================
# CSV TEMPLATE FUNCTIONS
# =============================================================================

def generate_csv_template(batch_mode):
    """Generate CSV template based on batch mode"""
    output_dir = "/mnt/user-data/outputs"
    
    templates = {
        "URLs": {
            "filename": "url_template.csv",
            "headers": ["url"],
            "sample_data": [
                ["https://example.com"],
                ["https://yourwebsite.com"],
                ["https://github.com/yourusername"]
            ]
        },
        "Wi-Fi": {
            "filename": "wifi_template.csv",
            "headers": ["ssid", "password", "security"],
            "sample_data": [
                ["MyHomeWiFi", "password123", "WPA2"],
                ["GuestNetwork", "guestpass456", "WPA"],
                ["OfficeNetwork", "office789", "WPA2"]
            ]
        },
        "vCards": {
            "filename": "vcard_template.csv",
            "headers": ["name", "phone", "email", "org"],
            "sample_data": [
                ["John Doe", "+1234567890", "john@example.com", "Acme Corp"],
                ["Jane Smith", "+0987654321", "jane@example.com", "Tech Inc"],
                ["Bob Johnson", "+1122334455", "bob@example.com", "StartupXYZ"]
            ]
        },
        "Custom": {
            "filename": "custom_template.csv",
            "headers": ["data"],
            "sample_data": [
                ["Your custom text here"],
                ["Another custom entry"],
                ["Third custom entry"]
            ]
        }
    }
    
    if batch_mode not in templates:
        return None, "Invalid batch mode selected"
    
    template = templates[batch_mode]
    filepath = os.path.join(output_dir, template["filename"])
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(template["headers"])
            writer.writerows(template["sample_data"])
        
        return filepath, f"✅ Template generated: {template['filename']}"
    except Exception as e:
        return None, f"❌ Error generating template: {str(e)}"


def validate_csv_structure(csv_file, expected_mode):
    """Validate CSV structure matches expected batch mode"""
    
    expected_columns = {
        "URLs": ["url"],
        "Wi-Fi": ["ssid", "password", "security"],
        "vCards": ["name", "phone", "email", "org"],
        "Custom": ["data"]
    }
    
    if expected_mode not in expected_columns:
        return False, "Invalid batch mode"
    
    try:
        with open(csv_file.name, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if headers is None:
                return False, "CSV file has no headers"
            
            # Normalize headers (lowercase, strip whitespace)
            normalized_headers = [h.lower().strip() for h in headers]
            expected = [col.lower() for col in expected_columns[expected_mode]]
            
            # Check if all expected columns are present
            missing_columns = [col for col in expected if col not in normalized_headers]
            
            if missing_columns:
                expected_cols_str = ", ".join(expected_columns[expected_mode])
                actual_cols_str = ", ".join(headers)
                return False, (
                    f"❌ CSV structure mismatch!\n\n"
                    f"**Expected columns for '{expected_mode}':** {expected_cols_str}\n"
                    f"**Your CSV has:** {actual_cols_str}\n\n"
                    f"**Missing columns:** {', '.join(missing_columns)}\n\n"
                    f"💡 **Solution:** Please download the correct template for '{expected_mode}' "
                    f"or select the QR code type that matches your CSV structure."
                )
            
            return True, "✅ CSV structure is valid"
    
    except Exception as e:
        return False, f"❌ Error reading CSV: {str(e)}"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def validate_url(url):
    """Validate if URL is properly formatted and reachable"""
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format"
        
        # Try to reach the URL (with timeout)
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                return True, "URL is reachable"
            else:
                return True, f"URL returned status {response.status_code}"
        except:
            return True, "URL format valid (connectivity check failed)"
    except:
        return False, "Invalid URL"


def check_password_strength(password):
    """Check Wi-Fi password strength"""
    if len(password) < 8:
        return "Weak - Too short (min 8 characters)", "🔴"
    
    score = 0
    if len(password) >= 12:
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[0-9]', password):
        score += 1
    if re.search(r'[^A-Za-z0-9]', password):
        score += 1
    
    if score >= 4:
        return "Strong", "🟢"
    elif score >= 3:
        return "Medium", "🟡"
    else:
        return "Weak", "🔴"


def save_to_history(qr_type, data_preview):
    """Save QR generation to history"""
    output_dir = "/mnt/user-data/outputs"
    history_file = os.path.join(output_dir, 'qr_history.json')
    
    try:
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
    except Exception:
        history = []
    
    history.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': qr_type,
        'preview': data_preview[:50]
    })
    
    # Keep only last 50 entries
    history = history[-50:]
    
    try:
        with open(history_file, 'w') as f:
            json.dump(history, f)
    except Exception:
        pass  # Fail silently if can't write
    
    return history


def load_history():
    """Load QR generation history"""
    output_dir = "/mnt/user-data/outputs"
    history_file = os.path.join(output_dir, 'qr_history.json')
    
    try:
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
            return history
        else:
            return []
    except Exception:
        return []


def get_analytics():
    """Get analytics from history"""
    history = load_history()
    if not history:
        return "No data yet"
    
    type_counts = {}
    for entry in history:
        qr_type = entry['type']
        type_counts[qr_type] = type_counts.get(qr_type, 0) + 1
    
    total = len(history)
    analytics_text = f"### 📊 QR Generation Analytics\n\n"
    analytics_text += f"**Total Generated:** {total}\n\n"
    analytics_text += "**By Type:**\n"
    
    for qr_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        analytics_text += f"- {qr_type}: {count} ({percentage:.1f}%)\n"
    
    return analytics_text


# =============================================================================
# DATA FORMATTING FUNCTIONS
# =============================================================================

def format_data(mode, *args):
    """Format data based on QR type"""
    if mode == "Link/URL":
        return args[0]
    
    elif mode == "Wi-Fi":
        ssid, password, security = args[1], args[2], args[3]
        return f"WIFI:S:{ssid};T:{security};P:{password};;"
    
    elif mode == "vCard (Contact)":
        name, phone, email, org = args[4], args[5], args[6], args[7]
        return (
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"FN:{name}\n"
            f"TEL:{phone}\n"
            f"EMAIL:{email}\n"
            f"ORG:{org}\n"
            "END:VCARD"
        )
    
    elif mode == "Email":
        dest, sub, body = args[8], args[9], args[10]
        return f"MAILTO:{dest}?subject={sub}&body={body}"
    
    elif mode == "SMS/Text":
        phone, message = args[11], args[12]
        return f"SMSTO:{phone}:{message}"
    
    elif mode == "Phone Call":
        phone = args[13]
        return f"TEL:{phone}"
    
    elif mode == "Cryptocurrency":
        crypto_type, address, amount = args[14], args[15], args[16]
        if crypto_type == "Bitcoin":
            return f"bitcoin:{address}?amount={amount}" if amount else f"bitcoin:{address}"
        elif crypto_type == "Ethereum":
            return f"ethereum:{address}?value={amount}" if amount else f"ethereum:{address}"
    
    elif mode == "Social Media":
        platform, username = args[17], args[18]
        platforms = {
            "Instagram": f"https://instagram.com/{username}",
            "Twitter/X": f"https://twitter.com/{username}",
            "LinkedIn": f"https://linkedin.com/in/{username}",
            "Facebook": f"https://facebook.com/{username}",
            "TikTok": f"https://tiktok.com/@{username}",
            "YouTube": f"https://youtube.com/@{username}"
        }
        return platforms.get(platform, f"https://{username}")
    
    elif mode == "Calendar Event":
        title, location, start, end, desc = args[19], args[20], args[21], args[22], args[23]
        return (
            "BEGIN:VEVENT\n"
            f"SUMMARY:{title}\n"
            f"LOCATION:{location}\n"
            f"DTSTART:{start.replace('-', '').replace(':', '')}00\n"
            f"DTEND:{end.replace('-', '').replace(':', '')}00\n"
            f"DESCRIPTION:{desc}\n"
            "END:VEVENT"
        )
    
    elif mode == "App Store":
        app_platform, app_id = args[24], args[25]
        if app_platform == "iOS":
            return f"https://apps.apple.com/app/id{app_id}"
        else:
            return f"https://play.google.com/store/apps/details?id={app_id}"
    
    return args[0]


# =============================================================================
# QR GENERATION FUNCTION
# =============================================================================

def generate_advanced_qr(
    mode,
    url,
    w_ssid, w_pass, w_sec,
    v_name, v_phone, v_email, v_org,
    e_to, e_sub, e_body,
    sms_phone, sms_msg,
    call_phone,
    crypto_type, crypto_addr, crypto_amt,
    social_platform, social_user,
    cal_title, cal_loc, cal_start, cal_end, cal_desc,
    app_platform, app_id,
    logo,
    error_level,
    module_style,
    qr_size
):
    """Generate QR code with advanced customization"""
    
    try:
        # Format data
        data = format_data(
            mode, url,
            w_ssid, w_pass, w_sec,
            v_name, v_phone, v_email, v_org,
            e_to, e_sub, e_body,
            sms_phone, sms_msg,
            call_phone,
            crypto_type, crypto_addr, crypto_amt,
            social_platform, social_user,
            cal_title, cal_loc, cal_start, cal_end, cal_desc,
            app_platform, app_id
        )
        
        # Save to history (optional - won't fail if it can't)
        try:
            save_to_history(mode, data)
        except Exception:
            pass  # Continue even if history save fails
        
        # Error correction mapping
        error_map = {
            "L (7%)": qrcode.constants.ERROR_CORRECT_L,
            "M (15%)": qrcode.constants.ERROR_CORRECT_M,
            "Q (25%)": qrcode.constants.ERROR_CORRECT_Q,
            "H (30%)": qrcode.constants.ERROR_CORRECT_H
        }
        
        # Module drawer mapping
        drawer_map = {
            "Rounded": RoundedModuleDrawer(),
            "Circles": CircleModuleDrawer(),
            "Squares": SquareModuleDrawer(),
            "Gapped Squares": GappedSquareModuleDrawer()
        }
        
        # Create QR code
        qr = qrcode.QRCode(
            error_correction=error_map[error_level],
            box_size=10,
            border=4
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Generate with style - always black on white
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=drawer_map[module_style],
            fill_color="#000000",
            back_color="#ffffff"
        ).convert("RGB")
        
        # Resize to specified size
        size_map = {
            "Small (300x300)": 300,
            "Medium (600x600)": 600,
            "Large (1200x1200)": 1200,
            "Print (2400x2400)": 2400
        }
        target_size = size_map[qr_size]
        img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        
        # Add logo if provided
        if logo is not None:
            logo_img = Image.open(logo)
            img_w, img_h = img.size
            logo_size = int(img_w * 0.18)
            logo_img = ImageOps.fit(logo_img, (logo_size, logo_size))
            
            # Create white background for logo
            logo_bg = Image.new('RGB', (logo_size + 20, logo_size + 20), 'white')
            logo_bg.paste(logo_img, (10, 10))
            
            img.paste(
                logo_bg,
                ((img_w - logo_size - 20) // 2, (img_h - logo_size - 20) // 2)
            )
        
        # Return just the image
        return img
    
    except Exception as e:
        # Return None on error
        return None


# =============================================================================
# BATCH GENERATION FUNCTION
# =============================================================================

def batch_generate_qr(csv_file, batch_mode, error_level, module_style):
    """Generate multiple QR codes from CSV file"""
    if csv_file is None:
        return None, "❌ Please upload a CSV file"
    
    # Validate CSV structure
    is_valid, validation_message = validate_csv_structure(csv_file, batch_mode)
    
    if not is_valid:
        return None, validation_message
    
    try:
        # Read CSV
        with open(csv_file.name, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return None, "❌ CSV file is empty (no data rows)"
        
        images = []
        status_messages = []
        status_messages.append(f"✅ CSV validated successfully")
        status_messages.append(f"📊 Processing {len(rows)} entries...\n")
        
        for idx, row in enumerate(rows):
            try:
                if batch_mode == "URLs":
                    data = row.get('url', '').strip()
                    if not data:
                        raise ValueError("Empty URL")
                    
                elif batch_mode == "Wi-Fi":
                    ssid = row.get('ssid', '').strip()
                    password = row.get('password', '').strip()
                    security = row.get('security', 'WPA').strip()
                    
                    if not ssid:
                        raise ValueError("Missing SSID")
                    
                    data = f"WIFI:S:{ssid};T:{security};P:{password};;"
                    
                elif batch_mode == "vCards":
                    name = row.get('name', '').strip()
                    phone = row.get('phone', '').strip()
                    email = row.get('email', '').strip()
                    org = row.get('org', '').strip()
                    
                    if not name:
                        raise ValueError("Missing name")
                    
                    data = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL:{phone}\nEMAIL:{email}\nORG:{org}\nEND:VCARD"
                    
                else:  # Custom
                    data = row.get('data', '').strip()
                    if not data:
                        raise ValueError("Empty data")
                
                # Generate QR
                error_map = {
                    "L (7%)": qrcode.constants.ERROR_CORRECT_L,
                    "M (15%)": qrcode.constants.ERROR_CORRECT_M,
                    "Q (25%)": qrcode.constants.ERROR_CORRECT_Q,
                    "H (30%)": qrcode.constants.ERROR_CORRECT_H
                }
                
                drawer_map = {
                    "Rounded": RoundedModuleDrawer(),
                    "Circles": CircleModuleDrawer(),
                    "Squares": SquareModuleDrawer(),
                    "Gapped Squares": GappedSquareModuleDrawer()
                }
                
                qr = qrcode.QRCode(error_correction=error_map[error_level])
                qr.add_data(data)
                qr.make(fit=True)
                
                # Always black on white
                img = qr.make_image(
                    image_factory=StyledPilImage,
                    module_drawer=drawer_map[module_style],
                    fill_color="#000000",
                    back_color="#ffffff"
                ).convert("RGB")
                
                img = img.resize((600, 600), Image.Resampling.LANCZOS)
                images.append(img)
                
                # Truncate preview for display
                preview = data[:40] + "..." if len(data) > 40 else data
                status_messages.append(f"✅ Row {idx+1}: {preview}")
                
            except Exception as e:
                status_messages.append(f"❌ Row {idx+1}: Error - {str(e)}")
        
        # Create gallery image
        if images:
            cols = min(3, len(images))
            rows_count = (len(images) + cols - 1) // cols
            
            gallery_width = 600 * cols + 20 * (cols + 1)
            gallery_height = 600 * rows_count + 20 * (rows_count + 1)
            
            gallery = Image.new('RGB', (gallery_width, gallery_height), 'white')
            
            for idx, img in enumerate(images):
                row = idx // cols
                col = idx % cols
                x = 20 + col * (600 + 20)
                y = 20 + row * (600 + 20)
                gallery.paste(img, (x, y))
            
            status = "\n".join(status_messages)
            summary = f"\n\n{'='*50}\n📊 Summary: {len(images)}/{len(rows)} QR codes generated successfully"
            return gallery, status + summary
        else:
            return None, "❌ No QR codes were generated\n\n" + "\n".join(status_messages)
    
    except Exception as e:
        return None, f"❌ Error processing CSV: {str(e)}"


# =============================================================================
# QR DECODER FUNCTION
# =============================================================================

def decode_qr(image_file):
    """Decode QR code from image"""
    if image_file is None:
        return "Please upload a QR code image"
    
    try:
        from pyzbar.pyzbar import decode
        img = Image.open(image_file)
        decoded_objects = decode(img)
        
        if decoded_objects:
            result = "### Decoded QR Code Data\n\n"
            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                result += f"**Type:** {obj.type}\n\n"
                result += f"**Data:**\n```\n{data}\n```\n\n"
            return result
        else:
            return "No QR code found in the image"
    except ImportError:
        return "⚠️ QR decoder requires 'pyzbar' library. Install with: pip install pyzbar"
    except Exception as e:
        return f"Error decoding QR code: {str(e)}"


# =============================================================================
# UI STYLING
# =============================================================================

css = """
.gradio-container { 
    background: linear-gradient(135deg, #0b0f19 0%, #1a1f2e 100%);
    font-family: 'Inter', sans-serif;
}
.input-group {
    border: 1px solid #2d3748;
    border-radius: 16px;
    padding: 20px;
    background: linear-gradient(145deg, #111827 0%, #1f2937 100%);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    margin-bottom: 15px;
}
.feature-box {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    border-radius: 12px;
    padding: 15px;
    border: 1px solid #475569;
}
.template-info {
    background: linear-gradient(135deg, #065f46 0%, #047857 100%);
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    border: 1px solid #059669;
}
"""

# =============================================================================
# GRADIO INTERFACE
# =============================================================================

with gr.Blocks(css=css, theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🌀 ROA Advanced QR Code Generator
        ### Professional QR code creation with extensive customization options
        """
    )
    
    with gr.Tabs() as tabs:
        
        # TAB 1: Single QR Generator
        with gr.Tab("🎯 Single QR Generator"):
            with gr.Row():
                with gr.Column(scale=1, elem_classes="input-group"):
                    mode = gr.Dropdown(
                        [
                            "Link/URL",
                            "Wi-Fi",
                            "vCard (Contact)",
                            "Email",
                            "SMS/Text",
                            "Phone Call",
                            "Cryptocurrency",
                            "Social Media",
                            "Calendar Event",
                            "App Store"
                        ],
                        label="📋 Select QR Type",
                        value="Link/URL"
                    )
                    
                    # URL Input
                    with gr.Group(visible=True) as url_box:
                        url_input = gr.Textbox(
                            label="🔗 Website URL",
                            placeholder="https://example.com"
                        )
                        url_status = gr.Textbox(label="URL Status", interactive=False, visible=False)
                        validate_btn = gr.Button("Validate URL", size="sm")
                    
                    # Wi-Fi Input
                    with gr.Group(visible=False) as wifi_box:
                        ssid = gr.Textbox(label="📶 Network Name (SSID)")
                        pw = gr.Textbox(label="🔐 Password", type="password")
                        pw_strength = gr.Textbox(label="Password Strength", interactive=False)
                        sec = gr.Radio(["WPA", "WPA2", "WEP", "nopass"], label="Security", value="WPA")
                    
                    # vCard Input
                    with gr.Group(visible=False) as vcard_box:
                        v_name = gr.Textbox(label="👤 Full Name")
                        v_phone = gr.Textbox(label="📱 Phone Number")
                        v_email = gr.Textbox(label="📧 Email")
                        v_org = gr.Textbox(label="🏢 Company / Organization")
                    
                    # Email Input
                    with gr.Group(visible=False) as email_box:
                        e_to = gr.Textbox(label="📧 Recipient Email")
                        e_sub = gr.Textbox(label="📝 Subject")
                        e_body = gr.TextArea(label="💬 Message Body")
                    
                    # SMS Input
                    with gr.Group(visible=False) as sms_box:
                        sms_phone = gr.Textbox(label="📱 Phone Number")
                        sms_msg = gr.TextArea(label="💬 Message")
                    
                    # Phone Call Input
                    with gr.Group(visible=False) as call_box:
                        call_phone = gr.Textbox(label="📞 Phone Number", placeholder="+1234567890")
                    
                    # Cryptocurrency Input
                    with gr.Group(visible=False) as crypto_box:
                        crypto_type = gr.Radio(["Bitcoin", "Ethereum"], label="₿ Cryptocurrency", value="Bitcoin")
                        crypto_addr = gr.Textbox(label="Wallet Address")
                        crypto_amt = gr.Textbox(label="Amount (Optional)")
                    
                    # Social Media Input
                    with gr.Group(visible=False) as social_box:
                        social_platform = gr.Dropdown(
                            ["Instagram", "Twitter/X", "LinkedIn", "Facebook", "TikTok", "YouTube"],
                            label="📱 Platform",
                            value="Instagram"
                        )
                        social_user = gr.Textbox(label="Username (without @)")
                    
                    # Calendar Event Input
                    with gr.Group(visible=False) as cal_box:
                        cal_title = gr.Textbox(label="📅 Event Title")
                        cal_loc = gr.Textbox(label="📍 Location")
                        cal_start = gr.Textbox(label="Start (YYYY-MM-DDTHH:MM)", placeholder="2024-12-25T10:00")
                        cal_end = gr.Textbox(label="End (YYYY-MM-DDTHH:MM)", placeholder="2024-12-25T12:00")
                        cal_desc = gr.TextArea(label="Description")
                    
                    # App Store Input
                    with gr.Group(visible=False) as app_box:
                        app_platform = gr.Radio(["iOS", "Android"], label="📱 Platform", value="iOS")
                        app_id = gr.Textbox(label="App ID / Package Name")
                    
                    gr.Markdown("---")
                    gr.Markdown("### 🎨 Customization Options")
                    
                    with gr.Accordion("Visual Customization", open=True):
                        logo_file = gr.Image(label="Center Logo (Optional)", type="filepath")
                        error_level = gr.Dropdown(
                            ["L (7%)", "M (15%)", "Q (25%)", "H (30%)"],
                            label="Error Correction Level",
                            value="H (30%)",
                            info="Higher levels allow more damage/obscuring"
                        )
                        module_style = gr.Dropdown(
                            ["Rounded", "Circles", "Squares", "Gapped Squares"],
                            label="Module Style",
                            value="Rounded"
                        )
                        
                        qr_size = gr.Dropdown(
                            ["Small (300x300)", "Medium (600x600)", "Large (1200x1200)", "Print (2400x2400)"],
                            label="QR Code Size",
                            value="Medium (600x600)"
                        )
                    
                    btn = gr.Button("🚀 Generate QR Code", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    output = gr.Image(label="📱 Your QR Code", type="pil")
        
        # TAB 2: Batch Generator
        with gr.Tab("📦 Batch Generator"):
            gr.Markdown(
                """
                ### Batch QR Code Generation
                Generate multiple QR codes at once using CSV files.
                
                **How it works:**
                1. Select your QR code type
                2. Download the matching CSV template
                3. Fill in your data
                4. Upload the completed CSV
                """
            )
            
            with gr.Row():
                with gr.Column():
                    batch_mode = gr.Dropdown(
                        ["URLs", "Wi-Fi", "vCards", "Custom"],
                        label="📋 Select Batch QR Type",
                        value="URLs"
                    )
                    
                    gr.Markdown(
                        """
                        <div class="template-info">
                        <strong>📥 Step 1: Download Template</strong><br>
                        Click on a template link below to open it in Google Sheets. Make a copy, fill in your data, then download as CSV.
                        </div>
                        """,
                        elem_classes="template-info"
                    )
                    
                    gr.Markdown("### 📋 CSV Templates")
                    
                    with gr.Row():
                        with gr.Column():
                            gr.HTML(
                                """
                                <div style="text-align: center; margin: 10px 0;">
                                    <strong>📄 URLs Template</strong><br>
                                    <small style="color: #888;">Columns: url</small><br><br>
                                    <a href="https://docs.google.com/spreadsheets/d/1TZSWa44DcY5JRG6K_FwqdUzlrASdMfHy7sG5zU1kSzk/edit?usp=sharing" target="_blank">
                                        <button style="width:100%; padding:12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                                       color:white; border:none; border-radius:8px; cursor:pointer; 
                                                       font-size:14px; font-weight:bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                            🔗 Open URLs Template
                                        </button>
                                    </a>
                                </div>
                                """
                            )
                        
                        with gr.Column():
                            gr.HTML(
                                """
                                <div style="text-align: center; margin: 10px 0;">
                                    <strong>👤 vCard Template</strong><br>
                                    <small style="color: #888;">Columns: name, phone, email, org</small><br><br>
                                    <a href="https://docs.google.com/spreadsheets/d/1bnxc3LqYF5Gmd39mKivsoSGH0Vwox4-7PiaoIllLDlo/edit?usp=sharing" target="_blank">
                                        <button style="width:100%; padding:12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                                       color:white; border:none; border-radius:8px; cursor:pointer; 
                                                       font-size:14px; font-weight:bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                            👤 Open vCard Template
                                        </button>
                                    </a>
                                </div>
                                """
                            )
                    
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("**📶 Wi-Fi Template**")
                            gr.Markdown("_Columns: ssid, password, security_")
                            generate_wifi_btn = gr.Button("📥 Download Wi-Fi Template", variant="secondary")
                            wifi_template_file = gr.File(label="Wi-Fi Template", interactive=False, visible=False)
                        
                        with gr.Column():
                            gr.Markdown("**📝 Custom Template**")
                            gr.Markdown("_Columns: data_")
                            generate_custom_btn = gr.Button("📥 Download Custom Template", variant="secondary")
                            custom_template_file = gr.File(label="Custom Template", interactive=False, visible=False)
                    
                    gr.Markdown(
                        """
                        ---
                        **💡 How to use Google Sheets templates:**
                        1. Click the template button to open it in a new tab
                        2. Go to **File → Make a copy** in Google Sheets
                        3. Fill in your data in the copy
                        4. Go to **File → Download → Comma Separated Values (.csv)**
                        5. Upload the CSV file below
                        
                        **For Wi-Fi and Custom templates:** Click the download button to get a CSV file directly.
                        """
                    )
                    
                    gr.Markdown("---")
                    
                    gr.Markdown(
                        """
                        **📤 Step 2: Upload Your Completed CSV**
                        """
                    )
                    
                    batch_csv = gr.File(label="Upload CSV File", file_types=[".csv"])
                    
                    validation_status = gr.Markdown("", visible=False)
                    
                    with gr.Row():
                        batch_error = gr.Dropdown(
                            ["L (7%)", "M (15%)", "Q (25%)", "H (30%)"],
                            label="Error Correction",
                            value="M (15%)"
                        )
                        batch_style = gr.Dropdown(
                            ["Rounded", "Circles", "Squares", "Gapped Squares"],
                            label="Style",
                            value="Rounded"
                        )
                    
                    batch_btn = gr.Button("🔄 Generate Batch QR Codes", variant="primary", size="lg")
                
                with gr.Column():
                    batch_output = gr.Image(label="Generated QR Codes Gallery")
                    batch_status = gr.Textbox(label="Batch Generation Log", lines=15)
        
        # TAB 3: QR Decoder
        with gr.Tab("🔍 QR Decoder"):
            gr.Markdown("### Decode existing QR codes")
            
            with gr.Row():
                with gr.Column():
                    decode_image = gr.Image(label="Upload QR Code Image", type="filepath")
                    decode_btn = gr.Button("🔓 Decode QR Code", variant="primary")
                
                with gr.Column():
                    decode_output = gr.Markdown(label="Decoded Data")
        
        # TAB 4: History & Analytics
        with gr.Tab("📊 Analytics & History"):
            with gr.Row():
                with gr.Column():
                    analytics_output = gr.Markdown("### No data yet")
                    refresh_analytics = gr.Button("🔄 Refresh Analytics")
                
                with gr.Column():
                    history_output = gr.JSON(label="Recent History")
                    refresh_history = gr.Button("🔄 Refresh History")
                    clear_history = gr.Button("🗑️ Clear History", variant="stop")
    
    # =============================================================================
    # EVENT HANDLERS
    # =============================================================================
    
    def toggle_inputs(choice):
        """Toggle input fields based on QR type selection"""
        return [
            gr.update(visible=(choice == "Link/URL")),
            gr.update(visible=(choice == "Wi-Fi")),
            gr.update(visible=(choice == "vCard (Contact)")),
            gr.update(visible=(choice == "Email")),
            gr.update(visible=(choice == "SMS/Text")),
            gr.update(visible=(choice == "Phone Call")),
            gr.update(visible=(choice == "Cryptocurrency")),
            gr.update(visible=(choice == "Social Media")),
            gr.update(visible=(choice == "Calendar Event")),
            gr.update(visible=(choice == "App Store"))
        ]
    
    mode.change(
        toggle_inputs,
        mode,
        [url_box, wifi_box, vcard_box, email_box, sms_box, call_box, crypto_box, social_box, cal_box, app_box]
    )
    
    def validate_url_handler(url):
        """Validate URL when button is clicked"""
        if not url:
            return gr.update(value="Please enter a URL", visible=True)
        
        is_valid, message = validate_url(url)
        return gr.update(value=message, visible=True)
    
    validate_btn.click(validate_url_handler, url_input, url_status)
    
    def check_password(password):
        """Check password strength"""
        if not password:
            return ""
        strength, emoji = check_password_strength(password)
        return f"{emoji} {strength}"
    
    pw.change(check_password, pw, pw_strength)
    
    # Single QR generation
    btn.click(
        generate_advanced_qr,
        inputs=[
            mode, url_input,
            ssid, pw, sec,
            v_name, v_phone, v_email, v_org,
            e_to, e_sub, e_body,
            sms_phone, sms_msg,
            call_phone,
            crypto_type, crypto_addr, crypto_amt,
            social_platform, social_user,
            cal_title, cal_loc, cal_start, cal_end, cal_desc,
            app_platform, app_id,
            logo_file, error_level, module_style,
            qr_size
        ],
        outputs=output
    )
    
    # Generate WiFi and Custom templates on button click
    def generate_wifi_template_handler():
        filepath, message = generate_csv_template("Wi-Fi")
        if filepath:
            return gr.update(value=filepath, visible=True)
        return gr.update(visible=False)
    
    def generate_custom_template_handler():
        filepath, message = generate_csv_template("Custom")
        if filepath:
            return gr.update(value=filepath, visible=True)
        return gr.update(visible=False)
    
    generate_wifi_btn.click(
        generate_wifi_template_handler,
        outputs=[wifi_template_file]
    )
    
    generate_custom_btn.click(
        generate_custom_template_handler,
        outputs=[custom_template_file]
    )
    
    # CSV validation on upload
    def validate_on_upload(csv_file, mode):
        if csv_file is None:
            return gr.update(value="", visible=False)
        
        is_valid, message = validate_csv_structure(csv_file, mode)
        
        if is_valid:
            return gr.update(value=f"✅ {message}", visible=True)
        else:
            return gr.update(value=message, visible=True)
    
    batch_csv.change(
        validate_on_upload,
        inputs=[batch_csv, batch_mode],
        outputs=[validation_status]
    )
    
    # Batch generation
    batch_btn.click(
        batch_generate_qr,
        inputs=[batch_csv, batch_mode, batch_error, batch_style],
        outputs=[batch_output, batch_status]
    )
    
    decode_btn.click(decode_qr, decode_image, decode_output)
    
    def refresh_analytics_handler():
        return get_analytics()
    
    def refresh_history_handler():
        return load_history()
    
    def clear_history_handler():
        output_dir = "/mnt/user-data/outputs"
        history_file = os.path.join(output_dir, 'qr_history.json')
        try:
            with open(history_file, 'w') as f:
                json.dump([], f)
            return []
        except Exception:
            return []
    
    refresh_analytics.click(refresh_analytics_handler, outputs=analytics_output)
    refresh_history.click(refresh_history_handler, outputs=history_output)
    clear_history.click(clear_history_handler, outputs=history_output)

# Launch the app
if __name__ == "__main__":
    initialize_app()  # Initialize app and create necessary files
    demo.launch(share=True)