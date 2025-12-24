# 🌀 ROA Advanced QR Code Generator

A professional, feature-rich QR code generator built with Gradio and Python. Create customized QR codes for multiple purposes with advanced styling options, batch processing, and analytics.

## ✨ Features

### 🎯 Multiple QR Code Types
- **Link/URL** - Website links with validation
- **Wi-Fi** - Network credentials with password strength checker
- **vCard** - Digital business cards
- **Email** - Pre-filled email messages
- **SMS/Text** - Pre-populated text messages
- **Phone Call** - Direct dial numbers
- **Cryptocurrency** - Bitcoin & Ethereum wallet addresses
- **Social Media** - Instagram, Twitter, LinkedIn, Facebook, TikTok, YouTube
- **Calendar Event** - iCal format events
- **App Store** - iOS App Store and Google Play links

### 🎨 Visual Customization
- **Module Styles**: Rounded, Circles, Squares, Gapped Squares
- **Gradient Colors**: Two-color gradient support
- **Logo Integration**: Center logo with white background
- **Frame Options**: Simple border, rounded border with custom text
- **Multiple Sizes**: 300x300 to 2400x2400 (print quality)
- **Error Correction**: L (7%), M (15%), Q (25%), H (30%)

### 📦 Batch Processing
- Generate multiple QR codes from CSV files
- Support for URLs, Wi-Fi networks, and vCards
- Gallery view of all generated codes
- Detailed status reporting

### 🔍 QR Decoder
- Upload and decode existing QR codes
- Display decoded data and type information

### 📊 Analytics & History
- Track generation statistics by type
- View recent QR code history
- Clear history option

### 🛡️ Smart Features
- **URL Validation** - Check if URLs are reachable
- **Password Strength Meter** - For Wi-Fi QR codes
- **History Tracking** - Keep last 50 generated codes
- **Error Handling** - Comprehensive error messages

## 🚀 Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. For QR decoding functionality, you may need system libraries:
```bash
# Ubuntu/Debian
sudo apt-get install libzbar0

# macOS
brew install zbar

# Windows
# Download from: http://zbar.sourceforge.net/
```

## 💻 Usage

### Running the Application

```bash
python advanced_qr_generator.py
```

The app will launch in your browser at `http://localhost:7860`

### Single QR Generation

1. Select your QR type from the dropdown
2. Fill in the required fields
3. Customize appearance (optional):
   - Choose module style
   - Set colors or gradients
   - Add a logo
   - Apply frame with text
   - Select output size
4. Click "Generate QR Code"
5. Download your QR code

### Batch Generation

1. Prepare a CSV file with the appropriate columns:
   
   **For URLs:**
   ```csv
   url
   https://example.com
   https://mywebsite.com
   ```
   
   **For Wi-Fi:**
   ```csv
   ssid,password,security
   MyNetwork,mypassword123,WPA
   GuestWiFi,guest2024,WPA2
   ```
   
   **For vCards:**
   ```csv
   name,phone,email,org
   John Doe,+1234567890,john@example.com,Acme Corp
   Jane Smith,+0987654321,jane@example.com,Tech Inc
   ```

2. Upload CSV file
3. Select batch mode
4. Choose styling options
5. Click "Generate Batch"
6. View gallery of all generated QR codes

### QR Decoding

1. Go to "QR Decoder" tab
2. Upload an image containing a QR code
3. Click "Decode QR Code"
4. View the decoded information

### Analytics

1. Go to "Analytics & History" tab
2. Click "Refresh Analytics" to see statistics
3. Click "Refresh History" to view recent codes
4. Use "Clear History" to reset data

## 📋 CSV Format Examples

### Example: urls.csv
```csv
url
https://github.com
https://google.com
https://stackoverflow.com
```

### Example: wifi_networks.csv
```csv
ssid,password,security
HomeNetwork,SecurePass123!,WPA2
GuestWiFi,guest2024,WPA
OfficeNet,CompanyPass456,WPA
```

### Example: business_cards.csv
```csv
name,phone,email,org
Alice Johnson,+1-555-0123,alice@company.com,TechCorp Inc
Bob Smith,+1-555-0456,bob@startup.io,StartupXYZ
Carol White,+1-555-0789,carol@business.com,Business Solutions
```

## 🎨 Customization Guide

### Color Gradients
- Set both color pickers to the same value for solid colors
- Use different colors for gradient effects
- Gradients flow from center (start color) to edges (end color)

### Module Styles
- **Rounded**: Soft, modern look
- **Circles**: Playful, unique appearance
- **Squares**: Classic, traditional QR
- **Gapped Squares**: Distinctive, spaced design

### Error Correction Levels
- **L (7%)**: Smallest QR, minimal redundancy
- **M (15%)**: Good balance (default for most uses)
- **Q (25%)**: Better for logos/decorations
- **H (30%)**: Best for logos, maximum redundancy

### Frame Styles
- **None**: Clean QR code without border
- **Simple Border**: Black rectangular frame
- **Rounded Border**: Modern rounded frame

## 🔧 Technical Details

### Built With
- **Gradio**: Web interface
- **qrcode**: QR code generation
- **Pillow (PIL)**: Image processing
- **pyzbar**: QR code decoding
- **requests**: URL validation

### File Structure
```
├── advanced_qr_generator.py  # Main application
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── examples/                  # Example CSV files
    ├── urls.csv
    ├── wifi.csv
    └── vcards.csv
```

## 💡 Tips & Best Practices

1. **Use High Error Correction** when adding logos (H 30%)
2. **Test QR Codes** before printing or distributing
3. **Keep URLs Short** for smaller, cleaner QR codes
4. **Use Print Size** (2400x2400) for physical materials
5. **Validate URLs** before generating to ensure they work
6. **Strong Wi-Fi Passwords** improve security
7. **Batch Mode** saves time for multiple codes

## 🐛 Troubleshooting

**QR code won't scan:**
- Increase error correction level
- Make logo smaller
- Use higher output resolution
- Ensure good contrast (dark on light)

**URL validation fails:**
- Check internet connection
- Verify URL format (include https://)
- Some servers may block validation requests

**Batch generation errors:**
- Check CSV format matches selected mode
- Ensure all required columns are present
- Remove special characters from data

**Decoder not working:**
- Install pyzbar library and system dependencies
- Ensure QR code image is clear and well-lit
- Try higher resolution image

## 📝 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📧 Support

For questions or issues, please create an issue in the repository.

---

**Made with ❤️ by ROA**
