# CDN Integration Guide for Online Price Intelligence System

This guide explains how to integrate a Content Delivery Network (CDN) to serve static assets and images globally with low latency.

## Overview

A CDN distributes your static content (images, CSS, JS, fonts) across geographically distributed servers, reducing load time and bandwidth costs.

- **Benefits**: 5-10x faster asset delivery, reduced server load, lower bandwidth costs
- **Typical Setup**: 5-10 minutes
- **Cost**: $0 (free tier) to $100+/month depending on usage

## Recommended CDNs

### 1. **Cloudinary** (Recommended for E-commerce)
- **Best for**: Product images, automatic optimization
- **Features**: Automatic format detection, responsive sizing, smart cropping
- **Pricing**: Free tier (25GB/month), then pay-as-you-go
- **Setup Time**: 5 minutes

#### Setup:
```javascript
// frontend/.env
VITE_CLOUDINARY_CLOUD_NAME=your_cloud_name
VITE_CLOUDINARY_API_KEY=your_api_key

// Usage in React:
const getCdnUrl = (publicId) => {
  return `https://res.cloudinary.com/${process.env.VITE_CLOUDINARY_CLOUD_NAME}/image/upload/w_600,h_400,f_auto,q_auto/${publicId}.jpg`;
};
```

### 2. **Imgix** (Recommended for Performance)
- **Best for**: Fast image delivery, real-time transformations
- **Features**: On-the-fly image optimization, format negotiation, compression
- **Pricing**: Free tier (50GB/month), then $0.08/GB
- **Setup Time**: 5 minutes

#### Setup:
```javascript
// frontend/.env
VITE_IMGIX_DOMAIN=your-domain.imgix.net

// Usage:
const getCdnUrl = (path) => {
  return `https://${process.env.VITE_IMGIX_DOMAIN}${path}?auto=format,compress&w=600&h=400&q=80`;
};
```

### 3. **AWS CloudFront** (Recommended for Scale)
- **Best for**: Enterprise, high volume
- **Features**: Global distribution, low cost, Lambda@Edge
- **Pricing**: Variable based on region ($0.084/GB - $0.140/GB)
- **Setup Time**: 15-30 minutes

#### Setup:
```javascript
// frontend/.env
VITE_CLOUDFRONT_URL=https://d1234abcd.cloudfront.net

// Usage:
const getCdnUrl = (path) => {
  return `${process.env.VITE_CLOUDFRONT_URL}${path}`;
};
```

### 4. **Bunny CDN** (Recommended for Cost)
- **Best for**: Budget-conscious, high bandwidth
- **Features**: Low cost ($0.01/GB), global coverage, image optimization
- **Pricing**: Cheapest option, pay-as-you-go
- **Setup Time**: 10 minutes

## Implementation Steps

### Step 1: Choose CDN and Create Account
1. Visit CDN website (cloudinary.com, imgix.com, etc.)
2. Sign up for free tier
3. Create project/distribution
4. Note your credentials

### Step 2: Update Environment Variables
```bash
# frontend/.env
VITE_CDN_PROVIDER=cloudinary  # or imgix, cloudfront, bunny
VITE_CDN_URL=https://your-cdn-url.com
VITE_CLOUDINARY_CLOUD_NAME=your_cloud_name  # if using Cloudinary
VITE_IMGIX_DOMAIN=your-domain.imgix.net      # if using Imgix

# backend/.env
CDN_PROVIDER=cloudinary
CDN_URL=https://your-cdn-url.com
CDN_UPLOAD_PRESET=your_upload_preset       # For Cloudinary
```

### Step 3: Update Image URLs in Code

```javascript
// Before (using local API):
<img src="/api/uploads/product.jpg" />

// After (using CDN):
<img src="https://res.cloudinary.com/{cloud}/image/upload/w_600/product.jpg" />
```

### Step 4: Update React Components

```javascript
// src/utils/cdnHelper.js
export const getCdnImageUrl = (filename, options = {}) => {
  const provider = process.env.VITE_CDN_PROVIDER;
  const cdnUrl = process.env.VITE_CDN_URL;
  
  const { width = 600, height = 400, quality = 'auto' } = options;
  
  switch(provider) {
    case 'cloudinary':
      return `https://res.cloudinary.com/${process.env.VITE_CLOUDINARY_CLOUD_NAME}/image/upload/w_${width},h_${height},f_auto,q_${quality}/${filename}`;
    
    case 'imgix':
      return `https://${process.env.VITE_IMGIX_DOMAIN}/${filename}?auto=format,compress&w=${width}&h=${height}&q=80`;
    
    case 'cloudfront':
      return `${cdnUrl}/${filename}`;
    
    default:
      return `/api/uploads/${filename}`;
  }
};

// Usage in components:
import { getCdnImageUrl } from '../utils/cdnHelper';

<img src={getCdnImageUrl('product.jpg', { width: 600, height: 400 })} />
```

### Step 5: Update Image Upload Endpoint

```python
# backend/app/main.py
from backend.app.image_optimization import optimizer

@app.post("/api/upload-image")
async def upload_image(file: UploadFile):
    # Save locally first
    local_path = f"static/uploads/{uuid.uuid4()}.jpg"
    
    # Option 1: Upload to CDN
    if use_cdn:
        cdn_url = await upload_to_cdn(file)
        return {"image_url": cdn_url}
    
    # Option 2: Use local + CDN for optimization
    # Optimize locally then sync to CDN
    optimized = optimizer.optimize_image(local_path)
    sync_to_cdn(optimized)
    
    return {"image_urls": optimized}
```

### Step 6: Enable CloudFront/Caching Headers

For local fallback, add caching headers:

```python
# backend-express/server.js
app.use((req, res, next) => {
  // Cache static assets for 30 days
  if (req.path.startsWith('/static')) {
    res.set('Cache-Control', 'public, max-age=2592000');
  }
  next();
});
```

## Advanced: CDN Upload Integration

### Automatic Upload on Image Processing

```python
# backend/app/tasks.py
@shared_task
def process_image_and_upload_to_cdn(image_path: str, product_id: str):
    # Process locally for ML
    predictions = predict_image(image_path)
    
    # Optimize multiple sizes
    optimized_urls = optimizer.optimize_image(image_path)
    
    # Upload to CDN
    cdn_urls = {}
    for size, local_path in optimized_urls.items():
        cdn_url = upload_to_cdn(local_path, f"products/{product_id}/{size}")
        cdn_urls[size] = cdn_url
    
    # Store CDN URLs in database
    db.update_product_images(product_id, cdn_urls)
    
    return cdn_urls
```

### Cloudinary Upload Preset (Recommended)

```javascript
// frontend/src/utils/cloudinaryUpload.js
export const uploadToCloudinary = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('upload_preset', process.env.VITE_CLOUDINARY_UPLOAD_PRESET);
  
  const response = await fetch(
    `https://api.cloudinary.com/v1_1/${process.env.VITE_CLOUDINARY_CLOUD_NAME}/image/upload`,
    {
      method: 'POST',
      body: formData
    }
  );
  
  const data = await response.json();
  return {
    url: data.secure_url,
    publicId: data.public_id,
    optimizedUrl: data.eager[0]?.secure_url // Pre-computed variations
  };
};
```

## Monitoring and Optimization

### Monitor CDN Performance

```javascript
// frontend/src/hooks/useCdnMetrics.js
export const useCdnMetrics = () => {
  const [metrics, setMetrics] = React.useState({});

  React.useEffect(() => {
    // Track image load times
    const images = document.querySelectorAll('img[data-cdn]');
    
    images.forEach(img => {
      img.addEventListener('load', () => {
        const loadTime = performance.now();
        console.log(`CDN image loaded in ${loadTime.toFixed(0)}ms`);
      });
    });
  }, []);

  return metrics;
};
```

### Expected Improvements

| Metric | Before CDN | After CDN | Improvement |
|--------|-----------|-----------|------------|
| Image Load Time | 2-3s | 200-500ms | 5-15x faster |
| Page Load Time | 4-5s | 1-2s | 2-3x faster |
| Bandwidth Cost | $500/month | $50/month | 90% savings |
| Server CPU | High | Low | 50% reduction |

## Troubleshooting

### Images Not Loading from CDN
1. Check CDN configuration in .env
2. Verify CORS headers
3. Check CloudFront distribution status
4. Verify origin bucket permissions

### Slow CDN Performance
1. Check edge location nearest to users
2. Enable compression in CDN settings
3. Use appropriate image formats (WebP vs JPEG)
4. Monitor CDN cache hit rates (target: >90%)

### CDN Billing Unexpectedly High
1. Enable image optimization to reduce file sizes
2. Set up caching headers (max-age: 30 days)
3. Monitor image delivery statistics
4. Consider switching CDN provider for cost

## Production Checklist

- [ ] CDN account created and configured
- [ ] Environment variables set in .env
- [ ] Image URLs updated in all components
- [ ] Upload endpoint modified to use CDN
- [ ] Caching headers configured
- [ ] CORS headers verified
- [ ] Performance monitoring enabled
- [ ] Fallback to local images configured
- [ ] Database updated with CDN URLs
- [ ] Testing with multiple image types
- [ ] Cost estimation reviewed
- [ ] Monitoring dashboard set up

## Cost Breakdown (Monthly)

### Cloudinary (Free + Paid)
- 25GB free tier
- $0.035/GB after free quota
- **Estimate**: $0-50/month for typical e-commerce

### Imgix
- $0.08/GB (minimum $0)
- **Estimate**: $10-100/month for typical e-commerce

### AWS CloudFront
- $0.084/GB (US region)
- $0.140/GB (other regions)
- **Estimate**: $50-200/month for typical e-commerce

### Bunny CDN
- $0.01/GB (cheapest)
- **Estimate**: $5-50/month for typical e-commerce

## Next Steps

1. Choose CDN provider based on your needs
2. Create account and get API credentials
3. Update environment files
4. Deploy to production
5. Monitor performance and costs
6. Optimize further based on metrics

## References

- [Cloudinary Docs](https://cloudinary.com/documentation)
- [Imgix Docs](https://docs.imgix.com/)
- [AWS CloudFront Docs](https://docs.aws.amazon.com/cloudfront/)
- [Bunny CDN Docs](https://docs.bunny.net/)

---

**Estimated Performance Improvement: 5-10x faster static asset delivery**
