"""ChartSpec - DSL for chart configuration"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any


Mark = Literal["histogram", "bar", "line", "scatter", "box"]
Agg = Literal["count", "sum", "mean", "min", "max", "median"]


class FieldSpec(BaseModel):
    """Field specification for chart axis"""
    name: str
    type: Literal["quantitative", "categorical", "temporal"]
    bin: Optional[int] = None  # for histogram
    time_unit: Optional[Literal["day", "week", "month", "quarter", "year"]] = None  # for temporal grouping
    topk: Optional[int] = None  # for category truncation
    sort: Optional[Literal["asc", "desc"]] = "desc"


class FilterSpec(BaseModel):
    """Filter specification for data filtering"""
    column: str
    op: Literal["==", "!=", "in", "notin", ">", ">=", "<", "<="]
    value: Any


class ChartSpec(BaseModel):
    """Chart specification DSL"""
    mark: Mark
    x: FieldSpec
    y: Optional[FieldSpec] = None
    agg: Optional[Agg] = "count"  # applies when y is None or categorical/temporal grouping
    filters: Optional[List[FilterSpec]] = None
    title: Optional[str] = None
    bins: Optional[int] = None  # global default for histogram (fallback for x.bin)
    width: int = 800
    height: int = 450

