annotation_rows=[["Output cover", "output_cover", [-20, 0, 210], true, 175.0], ["Front bearing hub", "front_bearing_hub", [-20, 0, 167], true, 150.0], ["Front pin carrier", "pin_front", [-20, 0, 135], true, 125.0], ["Upper wiggle shaft", "eccentric_hub_upper", [-84, 0, 110], true, 100.0], ["Disc B upper", "rotor_b_upper", [-20, 0, 104.0], true, 75.0], ["Disc B lower", "rotor_b_lower", [-20, 0, 64.5], true, 50.0], ["Disc A upper", "rotor_a_upper", [-20, 0, 24.5], true, 25.0], ["Lower wiggle shaft", "eccentric_hub_lower", [-84, 0, 0], true, 0.0], ["Output lobe ring", "output_casing", [164, 0, 30], true, -25.0], ["Disc A lower", "rotor_a_lower", [-20, 0, -15.0], true, -50.0], ["Coupling drive plate", "coupling_drive", [-84, 0, -32], true, -75.0], ["Coupling nut collar", "coupling_collar", [-84, 0, -65], true, -100.0], ["Rear pin carrier", "pin_rear", [-20, 0, -61], true, -125.0], ["Output casing base", "output_base", [158, 0, -34.6], true, -150.0], ["Motor faceplate", "motor_mount", [-20, 0, -125], true, -175.0], ["Casing screws", "4 x M3x35 socket caps; clamp cover / ring / base", [35.5, 35.5, 222.0], false, 175.0], ["Support fasteners", "3 x M3x25 rear; 3 x M3x25 posts; 3 x M3x16 hub", [16.5, 0, 191.0], false, 148.07692307692307], ["Front shaft bearing", "6704 / 20 x 27 x 4", [9, 0, 180.5], false, 121.15384615384616], ["Fixed guide bolts", "6 x M6 x 40 + nuts", [21, 0, 182.2], false, 94.23076923076923], ["Casing bearings", "2 x 6810 / 50 x 65 x 7", [29, 0, 178.1], false, 67.3076923076923], ["Hub joining bolt", "M6 x 35 + captive M6 nut", [-84, 0, 143.2], false, 40.38461538461539], ["Disc screws", "6 x M3 x 6 countersunk + nuts", [30, 0, 115.4], false, 13.461538461538453], ["Carrier spacers", "3 steel tubes / 6 OD x 3.2 ID x 15.5", [29, 0, 110], false, -13.461538461538453], ["Eccentric bearings", "2 x 6704 / 20 x 27 x 4", [9, 0, 86.0], false, -40.38461538461539], ["Disc bearing rows", "12 x 6700 / 10 x 15 x 4", [21, 0, 6.5], false, -67.30769230769232], ["Flange screws", "2 x M3 x 12 + side-loaded nuts", [8, 0, -6.5], false, -94.23076923076923], ["Flange coupling", "M5 bore / flange UP at 24 mm", [0, 0, -78], false, -121.15384615384613], ["Motor screws", "4 x M3 x 6 countersunk", [15.5, 15.5, -122.0], false, -148.0769230769231], ["NEMA 17 motor", "5 mm shaft", [0, 0, -176], false, -175.0]];
function ax(p,a)=[p[0],p[1]*cos(a)-p[2]*sin(a),p[1]*sin(a)+p[2]*cos(a)];
function ay(p,a)=[p[0]*cos(a)+p[2]*sin(a),p[1],-p[0]*sin(a)+p[2]*cos(a)];
function az(p,a)=[p[0]*cos(a)-p[1]*sin(a),p[0]*sin(a)+p[1]*cos(a),p[2]];
function screen(p)=ax(ay(az(p-$vpt,-$vpr[2]),-$vpr[1]),-$vpr[0]);
module annotation_line(a,b) {hull(){translate(a) circle(r=.25,$fn=12);translate(b) circle(r=.25,$fn=12);}}
if(is_undef(show_labels)||show_labels) color("#253746") translate($vpt) rotate($vpr) translate([0,0,250]) linear_extrude(.1) {
    color("#253746") for(row=annotation_rows) {
        p=screen(row[2]); left=row[3]; y=row[4];
        x=left?-335:195; join=left?-105:180;
        annotation_line([p[0],p[1]],[join,y]);
        annotation_line([join,y],[left?-175:190,y]);
        translate([p[0],p[1]]) circle(r=.9,$fn=16);
        translate([x,y+2]) text(row[0],size=5.8,font="Liberation Sans:style=Bold");
        translate([x,y-5.5]) text(row[1],size=4.1,font="Liberation Sans");
    }
    color("#253746") translate([-335,203]) text("VERSION 4  /  EXPLODED PART NAMES",size=8,font="Liberation Sans:style=Bold");
    color("#526779") translate([-335,190]) text("Printed parts: left     Hardware: right     Dimensions: mm",size=4.8,font="Liberation Sans");
}
