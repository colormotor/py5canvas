#!/usr/bin/env python3
#from . import run_sketch
import numpy as np

cfg = lambda: None
cfg.dragger_size = np.array([(13, 13)])
cfg.active = None
cfg.hover = None
cfg.draw_list = []
cfg.sketch = None

def dprint(*args):
    return
    print('gfxui:', *args)

def point_in_rect(p, pos, size):
    p, pos, size = np.array(p), np.array(pos), np.array(size)
    p = p-pos
    if np.all(p >= -size*0.5) and np.all(p <= size*0.5):
        return True
    return False

def add_to_drawlist(id, f):
    c = cfg.sketch.canvas
    def cb():
        c.push()
        if cfg.active == id or cfg.hover == id:
            c.fill('#ff0000')
        else:
            c.fill('#666666cc')
        f()
        c.pop()
    cfg.draw_list.append(cb)

def begin(sketch):
    cfg.draw_list = []
    cfg.hover = None
    cfg.sketch = sketch

def end():
    for f in cfg.draw_list:
        f()

def dragger(id, pos):
    c = cfg.sketch.canvas
    hover = point_in_rect(cfg.sketch.mouse_pos, pos, cfg.dragger_size)

    if hover and cfg.active is None:
        cfg.hover = id
        dprint('hover')
    if cfg.sketch.clicked and hover and cfg.active is None:
        dprint("Setting active", id, pos, cfg.sketch.dragging)
        cfg.active = id
    if not cfg.sketch.dragging and cfg.active == id:
        cfg.active = None
        dprint("Deactivating", id, pos)

    if cfg.sketch.dragging and cfg.active == id:
        dprint('Dragging', id, pos, cfg.sketch.mouse_delta)
        pos = cfg.sketch.mouse_pos.copy() #np.array(pos) + cfg.sketch.mouse_delta
    add_to_drawlist(id, lambda :(
        c.stroke(0),
        c.rectangle(*(pos-cfg.dragger_size*0.5), *(cfg.dragger_size))))

    return np.array(pos)

def angle_between(a, b):
    return np.arctan2( a[0]*b[1] - a[1]*b[0], a[0]*b[0] + a[1]*b[1] )

# def length_handle(id, theta, l, pos, start_theta=0.0, length_range=None, theta_range=None):
#     if length_range is not None:
#         l = np.clip(l, *length_range)
#     if theta_range is not None:
#         theta = np.clip(l, *theta_range)
#     theta = theta + start_theta
#     pos =
#     pos = dragger(id,
#         std::stringstream idstr;
#         idstr << groupId << "handle" << index;

#         ImGuiWindow* window = ImGui::GetCurrentWindow();
#         if (window->SkipItems)
#             return thetaLen;

#         ImGuiContext& g = *GImGui;
#         const ImGuiStyle& style = g.Style;
#         const ImGuiID id = window->GetID(idstr.str().c_str());
#         const float w = ImGui::CalcItemWidth();

#         ImVec2 vbase = ImVec2(::cos(startTheta), ::sin(startTheta));

#         bool res = false;
#         if(g.ActiveId == id)
#         {
#             if (g.IO.MouseDown[0])
#             {
#                 ImVec2 vmouse = ImVec2(ImGui::GetMousePos().x - pos.x, ImGui::GetMousePos().y - pos.y);
#                 thetaLen.x = (float)angleBetween(vbase, vmouse); //::atan2( ImGui::GetMousePos().y - pos.y, ImGui::GetMousePos().x - pos.x );

#                 if(maxThetaLen.x != 0)
#                     thetaLen.x = std::max( std::min(thetaLen.x, maxThetaLen.x), minThetaLen.x);

#                 thetaLen.y = std::max( std::min( length(ImGui::GetMousePos(), pos), maxThetaLen.y ), minThetaLen.y );
#                 res=mod=true;
#             }
#             else
#             {
#                 ImGui::SetActiveID(0, window);
#             }
#         }

#         // Specify object
#         ImVec2 hp = handlePos(pos, thetaLen.x+startTheta, thetaLen.y);
#         ImRect rect = rectFromCircle(hp, config.draggerSize*0.8);

#         ImGui::ItemSize(rect);
#         if(!ImGui::ItemAdd(rect, id))
#             return thetaLen;

#         // Check hovered
#         const bool hovered = ImGui::IsItemHovered(ImGuiHoveredFlags_RectOnly); //rect, id);
#         if (hovered)
#         {
#             ImGui::SetHoveredID(id);
#             if(g.IO.MouseClicked[0])
#             {
#                 ImGui::SetActiveID(id, window);
#                 ImGui::FocusWindow(window);
#             }
#         }

#         // Draw
#         ImU32 clr = getColor(hovered, selected);  //ImU32 clr = (g.ActiveId==id)?config.hoverColor:config.color; // ImGui::GetColorU32(g.ActiveId == id ? ImGuiCol_SliderGrabActive : ImGuiCol_SliderGrab);
#         window->DrawList->AddLine(pos, hp, config.lineColor);
#         drawDragger(window, rect, clr);
#         //window->DrawList->AddRectFilled(rect.Min, rect.Max, clr, config.rounding); //, rounding);

#         return thetaLen;
#     }
