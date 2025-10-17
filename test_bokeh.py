#!/usr/bin/env python3
"""
Test script to verify Bokeh functionality and compatibility
"""

import sys
import traceback


def test_bokeh_imports():
    """Test basic Bokeh imports"""
    try:
        import bokeh
        import pandas as pd
        import numpy as np
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        from bokeh.embed import components
        from bokeh.palettes import viridis
        from bokeh.transform import cumsum

        print(f"✓ Bokeh version: {bokeh.__version__}")
        print(f"✓ Pandas version: {pd.__version__}")
        print(f"✓ NumPy version: {np.__version__}")
        print("✓ All imports successful!")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return False


def test_bokeh_pie_chart():
    """Test creating a simple pie chart"""
    try:
        import pandas as pd
        import numpy as np
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        from bokeh.embed import components
        from bokeh.palettes import viridis
        from bokeh.transform import cumsum
        from math import pi

        # Create sample data
        data = {"substance": ["NaCl", "H2O", "HCl"], "cost": [100.0, 50.0, 75.0]}
        df = pd.DataFrame(data)

        # Calculate angles
        df["angle"] = df["cost"] / df["cost"].sum() * 2 * pi
        df["color"] = viridis(len(df))

        # Create ColumnDataSource with explicit data conversion
        source_data = {
            "substance": df["substance"].tolist(),
            "cost": df["cost"].tolist(),
            "angle": df["angle"].tolist(),
            "color": df["color"].tolist(),
        }
        source = ColumnDataSource(data=source_data)

        # Create pie chart
        p = figure(
            height=400,
            title="Test Pie Chart",
            toolbar_location=None,
            tools="hover",
            tooltips="@substance: @cost",
        )

        p.wedge(
            x=0,
            y=1,
            radius=0.4,
            start_angle=cumsum("angle", include_zero=True),
            end_angle=cumsum("angle"),
            line_color="white",
            fill_color="color",
            legend_field="substance",
            source=source,
        )

        script, div = components(p)

        print("✓ Pie chart creation successful!")
        print(f"✓ Script length: {len(script)} characters")
        print(f"✓ Div length: {len(div)} characters")
        return True

    except Exception as e:
        print(f"✗ Pie chart creation failed: {e}")
        traceback.print_exc()
        return False


def test_bokeh_bar_chart():
    """Test creating a simple bar chart"""
    try:
        import pandas as pd
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        from bokeh.embed import components

        # Create sample data
        data = {
            "analysis": ["Analysis A", "Analysis B", "Analysis C"],
            "count": [10, 15, 8],
        }
        df = pd.DataFrame(data)

        source_data = {
            "analysis": df["analysis"].tolist(),
            "count": df["count"].tolist(),
        }
        source = ColumnDataSource(data=source_data)

        # Create bar chart
        p = figure(
            y_range=df["analysis"].tolist(),
            height=400,
            title="Test Bar Chart",
            toolbar_location=None,
        )

        p.hbar(y="analysis", right="count", height=0.8, source=source, color="green")

        script, div = components(p)

        print("✓ Bar chart creation successful!")
        print(f"✓ Script length: {len(script)} characters")
        print(f"✓ Div length: {len(div)} characters")
        return True

    except Exception as e:
        print(f"✗ Bar chart creation failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("Testing Bokeh functionality...")
    print("=" * 50)

    results = []

    print("\n1. Testing imports...")
    results.append(test_bokeh_imports())

    print("\n2. Testing pie chart creation...")
    results.append(test_bokeh_pie_chart())

    print("\n3. Testing bar chart creation...")
    results.append(test_bokeh_bar_chart())

    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("✓ All tests passed! Bokeh should work correctly.")
        return 0
    else:
        print("✗ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
