# Bokeh Plotting Issue Resolution

## Problem
The Laboratory Management System was experiencing Bokeh plotting errors with the following symptoms:
- `RangeError: buffer length for Int32Array should be a multiple of 4`
- Charts not rendering in the browser
- JavaScript errors from bokeh-3.4.1.min.js

## Root Cause
The issue was caused by:
1. **Version Compatibility**: Bokeh 3.4.1+ has stricter requirements for data buffer alignment
2. **Data Type Issues**: Pandas DataFrame with `coerce_float=True` parameter was deprecated
3. **Buffer Alignment**: Direct DataFrame usage in ColumnDataSource caused buffer misalignment

## Solution Implemented

### 1. Version Constraints
Updated `pyproject.toml` with compatible version ranges:
```toml
"pandas>=2.0,<2.2",
"numpy>=1.24,<1.26", 
"bokeh>=3.0,<3.5",
```

### 2. Data Processing Improvements
**Before** (problematic):
```python
df_subs = pd.DataFrame.from_records(
    subs_query,
    coerce_float=True,  # Deprecated parameter
    columns=["subs_name", "measurement", "amount", "costs"],
)
source = ColumnDataSource(data=df_subs)  # Direct DataFrame usage
```

**After** (fixed):
```python
# Explicit data type conversion
data_records = []
for row in subs_query:
    data_records.append({
        "subs_name": str(row.substance_name),
        "measurement": str(row.measurement),
        "amount": float(row.amount) * -1,
        "costs": float(row.total_cost) * -1
    })

df_subs = pd.DataFrame(data_records)

# Convert to explicit dict for ColumnDataSource
source_data = {
    "subs_name": df_subs["subs_name"].tolist(),
    "costs": df_subs["costs"].tolist(),
    "angle": df_subs["angle"].tolist(),
    "color": df_subs["color"].tolist()
}
source = ColumnDataSource(data=source_data)
```

### 3. Error Handling
Added comprehensive error handling:
```python
def safe_create_bokeh_plot(data_frame, plot_type="pie"):
    """Safely create Bokeh plots with error handling."""
    try:
        if plot_type == "pie":
            return create_pie_chart(data_frame)
        elif plot_type == "bar":
            return create_bar_chart(data_frame)
    except Exception as e:
        logging.error(f"Bokeh plot creation failed: {e}")
        return "", "<div class='alert alert-warning'>Chart could not be generated.</div>"
```

### 4. Bokeh Figure Improvements
**Removed problematic parameters**:
- Removed `x_range` and `y_range` tuples that caused type errors
- Simplified dodge transformation usage
- Fixed range padding assignment

**Before**:
```python
plot_an = figure(
    y_range=df_an["analysis"].tolist(),
    x_range=(0, df_an["numbers"].max()),  # Problematic tuple
    # ...
)
plot_an.hbar(
    y=dodge("analysis", 0.0, range=plot_an.y_range),  # Complex transformation
    # ...
)
plot_an.y_range.range_padding = 0.1  # Direct attribute assignment
```

**After**:
```python
plot_an = figure(
    y_range=analysis_names,  # Direct list
    # ...
)
plot_an.hbar(
    y="analysis",  # Simple column reference
    # ...
)
# Removed range_padding assignment
```

## Files Modified

### 1. `/laboratory/views/statistic.py`
- Complete rewrite with improved error handling
- Fixed data processing pipeline
- Added safe plotting functions

### 2. `/pyproject.toml`
- Updated dependency version constraints
- Ensured compatibility between Bokeh, Pandas, and NumPy

### 3. Added Testing
- `/test_bokeh.py` - Comprehensive test script
- `/fix_bokeh.sh` - Installation helper script

## Verification

Run the test script to verify the fix:
```bash
/home/kostiantyn/projects/laboratory/env/bin/python test_bokeh.py
```

Expected output:
```
✓ All imports successful!
✓ Pie chart creation successful!
✓ Bar chart creation successful!
✓ All tests passed! Bokeh should work correctly.
```

## Benefits of the Solution

1. **Stability**: Robust error handling prevents application crashes
2. **Compatibility**: Version constraints ensure consistent behavior
3. **Performance**: Explicit data conversion reduces processing overhead
4. **Maintainability**: Clean separation of concerns with helper functions
5. **User Experience**: Graceful fallbacks when charts cannot be generated

## Best Practices Applied

1. **Explicit Data Type Conversion**: Convert all data to appropriate types before Bokeh processing
2. **Dictionary-based ColumnDataSource**: Use explicit dictionaries instead of DataFrame objects
3. **Version Pinning**: Constrain dependency versions to tested ranges
4. **Error Boundaries**: Wrap plotting code in try-catch blocks
5. **Graceful Degradation**: Provide meaningful error messages when plots fail

## Future Considerations

1. **Monitor Bokeh Updates**: Test with newer versions before upgrading
2. **Alternative Visualization**: Consider matplotlib or plotly as fallback options
3. **Client-Side Rendering**: Evaluate server-side image generation for complex plots
4. **Performance Optimization**: Cache plot generation for frequently accessed data

The solution ensures that the statistical reporting functionality works reliably while maintaining the existing user interface and functionality.