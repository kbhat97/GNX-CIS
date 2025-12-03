# 🎨 IMAGEN 3 (NANO BANANA PRO) SETUP GUIDE

**Date:** December 1, 2025  
**Model:** Google Imagen 3 (Nano Banana Pro)  
**Project:** gnx-cis (666167524553)

---

## ✅ **CONFIGURATION COMPLETE**

### **1. Project Settings**

- **Project ID:** `gnx-cis`
- **Project Number:** `666167524553`
- **Region:** `us-central1`
- **GCS Bucket:** `cis-linkedin-images` (auto-created)

### **2. Files Created/Updated**

- ✅ `utils/imagen_generator.py` - Imagen 3 generator
- ✅ `config.py` - Added GCP settings
- ✅ `requirements.txt` - Added Vertex AI package

---

## 🚀 **INSTALLATION STEPS**

### **Step 1: Install Dependencies**

```bash
cd c:\Users\16139\Linkedin_agent

# Install new packages
pip install google-cloud-aiplatform>=1.38.0

# Or install all requirements
pip install -r requirements.txt
```

### **Step 2: Authenticate with Google Cloud**

**Option A: Using gcloud (Recommended for development)**

```bash
# Login to Google Cloud
gcloud auth login

# Set default project
gcloud config set project gnx-cis

# Set application default credentials
gcloud auth application-default login
```

**Option B: Using Service Account (For production)**

```bash
# Download service account key from Google Cloud Console
# Save as: service-account-key.json

# Set environment variable
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json
```

### **Step 3: Enable Required APIs**

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=gnx-cis

# Enable Cloud Storage API (if not already enabled)
gcloud services enable storage.googleapis.com --project=gnx-cis

# Verify APIs are enabled
gcloud services list --enabled --project=gnx-cis | findstr aiplatform
gcloud services list --enabled --project=gnx-cis | findstr storage
```

### **Step 4: Update .env File**

Add these lines to your `.env`:

```bash
# Google Cloud Platform
GCP_PROJECT_ID="gnx-cis"
GCP_REGION="us-central1"
GCS_BUCKET_NAME="cis-linkedin-images"

# Optional: Service Account (if not using gcloud auth)
# GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

---

## 🧪 **TESTING**

### **Test 1: Quick Image Generation Test**

Create `test_imagen.py`:

```python
from utils.imagen_generator import create_linkedin_image

# Test image generation
image_url = create_linkedin_image(
    topic="AI in Healthcare",
    headline="95% of healthcare AI projects fail. Here's why.",
    style="professional"
)

if image_url:
    print(f"✅ Image generated successfully!")
    print(f"URL: {image_url}")
else:
    print("❌ Image generation failed")
```

Run:

```bash
python test_imagen.py
```

### **Test 2: Integration with Content Generation**

The image generator is automatically integrated. When you generate a post:

```bash
curl -X POST http://localhost:8080/posts/generate \
  -H "Authorization: Bearer dev_jwt_for_testing" \
  -H "Content-Type: application/json" \
  -d "{\"topic\": \"AI in Healthcare\", \"style\": \"Professional\"}"
```

The response will include:

```json
{
  "status": "success",
  "post_id": "post_20251201...",
  "content": "...",
  "image_path": "https://storage.googleapis.com/cis-linkedin-images/linkedin_posts/..."
}
```

---

## 💰 **COST MANAGEMENT**

### **Pricing**

- **Imagen 3:** ~$0.03 per image
- **GCS Storage:** ~$0.02/GB/month
- **GCS Bandwidth:** First 1GB free/month

### **Monthly Estimates**

| Usage              | Images | Cost |
| ------------------ | ------ | ---- |
| Light (100 posts)  | 100    | $3   |
| Medium (500 posts) | 500    | $15  |
| Heavy (1000 posts) | 1000   | $30  |

### **Optimization Tips**

1. **Cache similar images** - Don't regenerate identical content
2. **Batch generation** - Generate multiple variations at once
3. **Fallback to PIL** - Use PIL for simple branded templates
4. **Monitor usage** - Set up billing alerts

---

## 🎨 **USAGE EXAMPLES**

### **Example 1: Professional Post Image**

```python
from utils.imagen_generator import imagen_generator

url = imagen_generator.generate_linkedin_image(
    topic="Digital Transformation",
    headline="3 years ago, we made a decision that changed everything",
    style="professional",
    include_stats=False
)
```

### **Example 2: Quote Card**

```python
url = imagen_generator.generate_quote_card(
    quote="Innovation distinguishes between a leader and a follower",
    author="Steve Jobs"
)
```

### **Example 3: Statistic Highlight**

```python
url = imagen_generator.generate_stat_highlight(
    stat="34% faster",
    context="Order processing time after SAP implementation"
)
```

---

## 🔧 **TROUBLESHOOTING**

### **Issue: "Vertex AI not initialized"**

**Solution:**

```bash
# Check if authenticated
gcloud auth list

# Re-authenticate if needed
gcloud auth application-default login

# Verify project
gcloud config get-value project
```

### **Issue: "Permission denied" errors**

**Solution:**

```bash
# Grant necessary permissions to your account
gcloud projects add-iam-policy-binding gnx-cis \
  --member="user:your-email@gmail.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding gnx-cis \
  --member="user:your-email@gmail.com" \
  --role="roles/storage.admin"
```

### **Issue: "Bucket already exists" (owned by another project)**

**Solution:**

```bash
# Use a unique bucket name in .env
GCS_BUCKET_NAME="cis-linkedin-images-gnx-666167524553"
```

### **Issue: "API not enabled"**

**Solution:**

```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com --project=gnx-cis
gcloud services enable storage.googleapis.com --project=gnx-cis
```

---

## 📊 **MONITORING**

### **View Generated Images**

```bash
# List all generated images
gsutil ls gs://cis-linkedin-images/linkedin_posts/

# View image details
gsutil ls -l gs://cis-linkedin-images/linkedin_posts/
```

### **Check Costs**

1. Go to: https://console.cloud.google.com/billing
2. Select project: `gnx-cis`
3. View: Vertex AI and Cloud Storage costs

### **Set Up Billing Alerts**

```bash
# Set budget alert at $50/month
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="CIS Image Generation Budget" \
  --budget-amount=50USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

---

## ✅ **VERIFICATION CHECKLIST**

Before going live, verify:

- [ ] `gcloud auth application-default login` completed
- [ ] Vertex AI API enabled
- [ ] Cloud Storage API enabled
- [ ] `.env` file updated with GCP settings
- [ ] `pip install google-cloud-aiplatform` completed
- [ ] Test image generation successful
- [ ] GCS bucket created and accessible
- [ ] Images publicly accessible
- [ ] Billing alerts configured
- [ ] Integration tests passing (11/11)

---

## 🎯 **NEXT STEPS**

1. **Run Setup:**

   ```bash
   # Authenticate
   gcloud auth application-default login

   # Install packages
   pip install google-cloud-aiplatform

   # Enable APIs
   gcloud services enable aiplatform.googleapis.com storage.googleapis.com
   ```

2. **Test Generation:**

   ```bash
   python test_imagen.py
   ```

3. **Integrate with Posts:**

   - Images will automatically generate when creating posts
   - Check `image_path` in API responses

4. **Monitor Usage:**
   - Check GCS bucket for generated images
   - Monitor costs in Google Cloud Console

---

## 📞 **SUPPORT**

**Google Cloud Console:**

- Project: https://console.cloud.google.com/home/dashboard?project=gnx-cis
- Vertex AI: https://console.cloud.google.com/vertex-ai?project=gnx-cis
- Storage: https://console.cloud.google.com/storage/browser?project=gnx-cis

**Documentation:**

- Vertex AI Imagen: https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview
- Cloud Storage: https://cloud.google.com/storage/docs

---

**🎉 Ready to generate amazing LinkedIn images with Imagen 3!**
