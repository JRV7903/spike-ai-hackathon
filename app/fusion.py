import pandas as pd
from urllib.parse import urlparse

def normalize_url(url: str) -> str:
    """
    Normalizes a URL to a path for joining.
    e.g. 'https://example.com/pricing/' -> '/pricing'
    e.g. '/pricing' -> '/pricing'
    """
    if not url:
        return ""
    
    # If it's already a path
    if url.startswith("/"):
        path = url
    else:
        try:
            parsed = urlparse(url)
            path = parsed.path
        except:
            path = url
            
    # Normalize trailing slash (remove it for consistent join, unless root)
    if path != "/" and path.endswith("/"):
        path = path[:-1]
        
    return path.lower()

def fuse_data(analytics_data: list[dict], seo_data: list[dict]) -> dict:
    """
    Fuses Analytics and SEO data using pandas.
    Returns a dict with 'fused_data' (list of dicts) and 'fusion_log' (str).
    """
    if not analytics_data or not seo_data:
        return {
            "fused_data": analytics_data or seo_data or [],
            "fusion_log": "Skipped fusion: One or both datasets are empty."
        }

    df_analytics = pd.DataFrame(analytics_data)
    df_seo = pd.DataFrame(seo_data)
    
    # Identify join keys
    ana_key = None
    for col in df_analytics.columns:
        if col.lower() in ['pagepath', 'fullpageurl', 'page_path', 'page_location']:
            ana_key = col
            break
            
    seo_key = None
    for col in df_seo.columns:
        if col.lower() in ['address', 'url', 'uri']:
            seo_key = col
            break
            
    if not ana_key or not seo_key:
        return {
            "fused_data": [],
            "fusion_log": f"Fusion failed: Could not identify join keys. Analytics keys: {list(df_analytics.columns)}, SEO keys: {list(df_seo.columns)}"
        }
        
    # Normalize keys for joining
    df_analytics['join_key'] = df_analytics[ana_key].apply(normalize_url)
    df_seo['join_key'] = df_seo[seo_key].apply(normalize_url)
    
    try:
        merged_df = pd.merge(df_analytics, df_seo, on='join_key', how='inner', suffixes=('_analytics', '_seo'))
        
        # Drop join key
        merged_df = merged_df.drop(columns=['join_key'])
        
        fused_data = merged_df.to_dict(orient='records')
        
        return {
            "fused_data": fused_data,
            "fusion_log": f"Successfully fused {len(fused_data)} records using keys '{ana_key}' (Analytics) and '{seo_key}' (SEO)."
        }
    except Exception as e:
        return {
            "fused_data": [],
            "fusion_log": f"Fusion error: {str(e)}"
        }
