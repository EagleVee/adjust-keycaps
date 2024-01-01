from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Builder
from OCC.Core.gp import gp_Trsf, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Extend.DataExchange import read_step_file
from OCC.Display.SimpleGui import init_display
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
import random

from OCC.Extend.TopologyUtils import TopologyExplorer


def write_step_file(shape, filename):
    """Writes the given shape to a STEP file."""
    step_writer = STEPControl_Writer()
    step_writer.Transfer(shape, STEPControl_AsIs)
    step_writer.Write(filename)


def align_and_combine_step_files(filenames, offset_x):
    """Reads multiple STEP files, aligns, and combines them into one."""
    compound = TopoDS_Compound()
    builder = TopoDS_Builder()
    builder.MakeCompound(compound)

    x_offset = 0
    for filename in filenames:
        shape = read_step_file(filename)
        transform = gp_Trsf()
        transform.SetTranslation(gp_Vec(x_offset, 0, 0))
        transformed_shape = BRepBuilderAPI_Transform(shape, transform, True).Shape()
        builder.Add(compound, transformed_shape)
        x_offset += 18.1 + offset_x

    return compound


def display_compound(compound):
    display.EraseAll()
    t = TopologyExplorer(compound)
    for solid in t.solids():
        color = Quantity_Color(
            random.random(), random.random(), random.random(), Quantity_TOC_RGB
        )
        display.DisplayColoredShape(solid, color)
    display.FitAll()


step_files = ['./profiles/cherry/r1/r1_100.step', './profiles/cherry/r1/r1_200.step']

if __name__ == "__main__":
    combined_shape = align_and_combine_step_files(step_files, 0.95)

    # Export to a new STEP file
    output_file = 'combined_objects.step'
    write_step_file(combined_shape, output_file)
    display, start_display, add_menu, add_function_to_menu = init_display()
    start_display()
    display_compound(compound=combined_shape)
