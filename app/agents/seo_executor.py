import pandas as pd
import numpy as np

def execute_seo_plan(df: pd.DataFrame, plan: dict) -> list[dict]:
    """
    Executes a structured SEO query plan on a DataFrame safely.
    """
    if not plan:
        return []

    if not plan:
        return []

    result_df = df.copy()
    
    filters = plan.get("filters", [])
    for f in filters:
        col = f.get("column")
        op = f.get("operator")
        val = f.get("value")
        
        if col not in result_df.columns:
            continue
            
        try:
            if op == "==":
                result_df = result_df[result_df[col] == val]
            elif op == "!=":
                result_df = result_df[result_df[col] != val]
            elif op == ">":
                result_df = result_df[pd.to_numeric(result_df[col], errors='coerce') > val]
            elif op == "<":
                result_df = result_df[pd.to_numeric(result_df[col], errors='coerce') < val]
            elif op == ">=":
                result_df = result_df[pd.to_numeric(result_df[col], errors='coerce') >= val]
            elif op == "<=":
                result_df = result_df[pd.to_numeric(result_df[col], errors='coerce') <= val]
            elif op == "contains":
                result_df = result_df[result_df[col].astype(str).str.contains(str(val), case=False, na=False)]
            elif op == "not_contains":
                result_df = result_df[~result_df[col].astype(str).str.contains(str(val), case=False, na=False)]
            elif op == "is_null":
                result_df = result_df[result_df[col].isnull() | (result_df[col] == "")]
            elif op == "is_not_null":
                result_df = result_df[result_df[col].notnull() & (result_df[col] != "")]
        except Exception:
            pass

    group_by = plan.get("group_by")
    aggregations = plan.get("aggregations", [])
    
    if group_by and group_by in result_df.columns:
        agg_dict = {}
        for agg in aggregations:
            col = agg.get("column")
            metric = agg.get("metric")
            if col not in result_df.columns and metric != "count":
                continue
                
            if metric == "count":
                agg_dict[col or group_by] = "count"
            elif metric == "sum":
                agg_dict[col] = "sum"
            elif metric == "mean":
                agg_dict[col] = "mean"
            elif metric == "min":
                agg_dict[col] = "min"
            elif metric == "max":
                agg_dict[col] = "max"
            elif metric == "unique_count":
                agg_dict[col] = "nunique"
            elif metric == "list":
                agg_dict[col] = lambda x: list(x)
        
        if agg_dict:
            try:
                result_df = result_df.groupby(group_by).agg(agg_dict).reset_index()
            except Exception:
                 pass
                 
    elif aggregations:
        summary = {}
        for agg in aggregations:
            col = agg.get("column")
            metric = agg.get("metric")
            
            if col and col not in result_df.columns: 
                continue

            try:
                if metric == "count":
                    summary[f"count_{col}"] = len(result_df)
                elif metric == "sum":
                    summary[f"sum_{col}"] = pd.to_numeric(result_df[col], errors='coerce').sum()
                elif metric == "mean":
                    summary[f"mean_{col}"] = pd.to_numeric(result_df[col], errors='coerce').mean()
                elif metric == "unique_count":
                    summary[f"unique_{col}"] = result_df[col].nunique()
            except:
                pass
        
        if summary:
            return [summary]

    sort = plan.get("sort")
    if sort:
        col = sort.get("column")
        ascending = sort.get("ascending", True)
        if col in result_df.columns:
            result_df = result_df.sort_values(by=col, ascending=ascending)

    limit = plan.get("limit", 100)
    if isinstance(limit, int):
        result_df = result_df.head(limit)

    return result_df.fillna("").to_dict(orient="records")
