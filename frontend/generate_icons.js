const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const inputImagePath = path.join(__dirname, 'public', 'logo.png');
const appDir = path.join(__dirname, 'src', 'app');

async function generateIcons() {
  try {
    if (!fs.existsSync(appDir)) {
      fs.mkdirSync(appDir, { recursive: true });
    }

    // Generate icon.png (32x32) for standard browsers
    await sharp(inputImagePath)
      .resize(32, 32)
      .toFile(path.join(appDir, 'icon.png'));
    
    // Generate apple-icon.png (180x180) for iOS
    await sharp(inputImagePath)
      .resize(180, 180)
      .toFile(path.join(appDir, 'apple-icon.png'));
    
    console.log('Successfully generated icon.png and apple-icon.png in src/app directory.');

    await sharp(inputImagePath)
      .resize(32, 32)
      .png()
      .toFile(path.join(appDir, 'favicon.ico'));
    
    console.log('Successfully generated favicon.ico');

  } catch (error) {
    console.error('Error generating icons:', error);
    process.exit(1);
  }
}

generateIcons();
