import math
from shapely.geometry import Polygon
import plotly.graph_objects as go
from numpy import deg2rad, rad2deg
from pandas import DataFrame

def create_rectangle(cx, cy, angle, lf, wl, lr, wr):
    """Creates the four corners of the rectangle given the center, angle, and dimensions."""
    corners = [
        (-lr, -wr),
        (lf, -wr),
        (lf, wl),
        (-lr, wl)
    ]
    
    # Rotate and translate the corners to the global coordinate system
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    transformed_corners = [
        (
            cx + cos_a * x - sin_a * y,
            cy + sin_a * x + cos_a * y
        )
        for x, y in corners
    ]
    
    return Polygon(transformed_corners)

def overlap(cx1, cy1, angle1, lf1, wl1, lr1, wr1, 
            cx2, cy2, angle2, lf2, wl2, lr2, wr2):
    """Checks if two rectangles overlap."""
    rect1 = create_rectangle(cx1, cy1, angle1, lf1, wl1, lr1, wr1)
    rect2 = create_rectangle(cx2, cy2, angle2, lf2, wl2, lr2, wr2)
    return rect1.intersects(rect2)

def is_overlap(cx1, cy1, t1, lf1, wl1, lr1, wr1, cx2, cy2, t2, lf2, wl2, lr2, wr2):
    def transform_and_check(cx1, cy1, t1, lf1, wl1, lr1, wr1, cx2, cy2, t2, lf2, wl2, lr2, wr2):
        # Define the corners of the first rectangle in its local coordinate system
        corners_y = [wl1, -wr1, -wr1, wl1]
        corners_x = [-lr1, -lr1, lf1, lf1]
        
        ct1 = math.cos(t1)
        st1 = math.sin(t1)
        ct2 = math.cos(t2)
        st2 = math.sin(t2)
        
        # Rectangle bounds in local coordinate system
        min_y = -wr2
        max_y = wl2
        min_x = -lr2
        max_x = lf2
        
        # Transform these corners to the global coordinate system
        for i in range(4):
            x = corners_x[i]
            y = corners_y[i]
            
            # Rotate corner of rect1 around the center
            x_rot = (x * ct1) - (y * st1)
            y_rot = (x * st1) + (y * ct1)
            
            # Translate corner to the global coordinate system
            x_global = x_rot + cx1
            y_global = y_rot + cy1
            
            # Translate corner of rect1 to the rect2 center
            tx = x_global - cx2
            ty = y_global - cy2
            
            # Rotate corner of rect1 to the rect2's local coordinate system
            lx = (tx * ct2) + (ty * st2)
            ly = (-tx * st2) + (ty * ct2)
            
            # Check if the transformed point lies within the bounds of the second rectangle
            if min_x <= lx <= max_x and min_y <= ly <= max_y:
                return True
        return False
    
    return transform_and_check(cx1, cy1, t1, lf1, wl1, lr1, wr1, cx2, cy2, t2, lf2, wl2, lr2, wr2) or \
           transform_and_check(cx2, cy2, t2, lf2, wl2, lr2, wr2, cx1, cy1, t1, lf1, wl1, lr1, wr1)

def caller():
    '''
    test_cases = [
        # Format: (cx1, cy1, angle1, lf1, wl1, lr1, wr1, cx2, cy2, angle2, lf2, wl2, lr2, wr2)
        (2, 2, 0, 2, 1, 2, 1, 6, 2, 0, 3, 1.5, 3, 1.5),
        (10, 10, math.pi / 4, 1, 1, 1, 1, 14, 14, -math.pi / 4, 2.5, 1.5, 2.5, 1.5),
        (20, 2, 0, 2, 1, 2, 1, 24, 4, 0, 2.5, 1.5, 2.5, 1.5)
    ]
    '''

    rx = 2
    ry = 4
    o1 = 0.0
    o2 = 0.0
    lf1 = 1.0
    wl1 = 1.0
    lr1 = 1.0
    wr1 = 2.0
    ad = 0
    fac = 1
    lsy = [0,6, 10, 14, 22, 34, 44, 50, 56, 62, 70]
    lsx = [1, 1, 1, 1, 1, 1, 1, 1, 3, 4, 5]
    lfs2 = [0, 0, 0, 0, 0, 0, -0.5, -0.8, 2.0, 3.0, 4.0]
    wls2 = [-0.5, -0.5, -0.5, -0.5, 3.0, 4.0, -0.5, -0.5, 0, 0, 0]
    lrs2 = [0, 0, -0.5, -0.7, 0, 0, -0.5, -0.8, 2.0, 3.0, 4.0]
    wrs2 = [0, 0, -1.5, -1.7, 2.0, 3.0, 0, 0, -1.0, -1.0, -1.0]

    test_cases = []
    for i in range(len(lsx)):
        test_cases.append([rx, ry+lsy[i] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[i] , ry+fac*ad+lsy[i] ,  o2,  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
    '''
    test_cases = [
        (rx, ry+lsy[0] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[0] , ry+fac*ad+lsy[0] ,  o2,  lf1+lfs2[0] , wl1+wls2[0] , lr1+lrs2[0] , wr1+wrs2[0] ),    
        (rx, ry+lsy[1] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[1] , ry+fac*ad+lsy[1] ,  o2,  lf1+lfs2[1] , wl1+wls2[1] , lr1+lrs2[1] , wr1+wrs2[1] ),
        (rx, ry+lsy[2] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[2] , ry+fac*ad+lsy[2] ,  o2,  lf1+lfs2[2] , wl1+wls2[2] , lr1+lrs2[2] , wr1+wrs2[2] ),
        (rx, ry+lsy[3] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[3] , ry+fac*ad+lsy[3] ,  o2,  lf1+lfs2[3] , wl1+wls2[3] , lr1+lrs2[3] , wr1+wrs2[3] ),
        (rx, ry+lsy[4] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[4] , ry+fac*ad+lsy[4] ,  o2,  lf1+lfs2[4] , wl1+wls2[4] , lr1+lrs2[4] , wr1+wrs2[4] ),
        (rx, ry+lsy[5] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[5] , ry+fac*ad+lsy[5] ,  o2,  lf1+lfs2[5] , wl1+wls2[5] , lr1+lrs2[5] , wr1+wrs2[5] ),
        (rx, ry+lsy[6] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[6] , ry+fac*ad+lsy[6] ,  o2,  lf1+lfs2[6] , wl1+wls2[6] , lr1+lrs2[6] , wr1+wrs2[6] ),
        (rx, ry+lsy[7] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[7] , ry+fac*ad+lsy[7] ,  o2,  lf1+lfs2[7] , wl1+wls2[7] , lr1+lrs2[7] , wr1+wrs2[7] ),
        (rx, ry+lsy[8] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[8] , ry+fac*ad+lsy[8] ,  o2,  lf1+lfs2[8] , wl1+wls2[8] , lr1+lrs2[8] , wr1+wrs2[8] ),
        (rx, ry+lsy[9] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[9] , ry+fac*ad+lsy[9] ,  o2,  lf1+lfs2[9] , wl1+wls2[9] , lr1+lrs2[9] , wr1+wrs2[9] ),
        (rx, ry+lsy[10],  o1,  lf1, wl1, lr1, wr1,      rx+lsx[10], ry+fac*ad+lsy[10],  o2,  lf1+lfs2[10], wl1+wls2[10], lr1+lrs2[10], wr1+wrs2[10])
    ]
    '''
    #right of centre
    rx+=12
    ad = 1
    fac = 1
    for i in range(len(lsx)):
        test_cases.append([rx, ry+lsy[i] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[i] , ry+fac*ad+lsy[i] ,  o2,  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])

    # left of centre
    rx+=12
    ad = 1
    fac = -1
    for i in range(len(lsx)):
        test_cases.append([rx, ry+lsy[i] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[i] , ry+fac*ad+lsy[i] ,  o2,  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])

    # below centre
    rx+=22
    ad = 0
    fac = 1
    for i in range(len(lsx)):
        x1 = rx+lsx[i]
        x2 = rx
        test_cases.append([rx, ry+lsy[i] ,  o1,  lf1, wl1, lr1, wr1,      2*x2 -x1 , ry+fac*ad+lsy[i] ,  o2,  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])

    # 10 deg difference
    # test_cases = []
    o2 = deg2rad(10)
    os1 = [i for i in range(-180, 179, 45)]
    os2 = [i for i in range(0, 31, 10)]

    print(os1)
    print(os2)
    # exit()
    ad = 0
    fac = 0
    for o1 in os1:
        for o2 in os2:
            if(o1==0 and o2 ==0):
                continue
            o2 +=o1
            rx+=12
            for i in range(len(lsx)):
                if(o1 == -180 and o2 == o1+30 and i == 10):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-1 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -135 and o2 == o1+0 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.5 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -135 and o2 == o1+10 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -135 and o2 == o1+20 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -135 and o2 == o1+30 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -90 and o2 == o1+0 and i in [8, 9]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -90 and o2 == o1+0 and i == 10):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-3.5 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -90 and o2 == o1+0 and i < 6):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i] , ry+fac*ad+lsy[i]-0.5 ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -90 and o2 == o1+10 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-3.0 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -90 and o2 == o1+20 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-3.0 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -90 and o2 == o1+30 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-3.0 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -45 and o2 == o1+0 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -45 and o2 == o1+10 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -45 and o2 == o1+20 and i in [7, 8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -45 and o2 == o1+30 and i in [8, 9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == -45 and o2 == o1+30 and i == 7):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-1 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 45 and o2 == o1+0 and i in [9,10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-1.5 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 45 and o2 == o1+10 and i in [9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 45 and o2 == o1+20 and i in [9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 45 and o2 == o1+30 and i in [9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 90 and o2 == o1+0 and i in [9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 90 and o2 == o1+0 and i == 8):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-0.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 90 and o2 == o1+0 and i < 6):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i] , ry+fac*ad+lsy[i]-0.5 ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 90 and o2 == o1+10 and i in [9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 90 and o2 == o1+20 and i in [9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 90 and o2 == o1+30 and i in [9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.7 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                elif(o1 == 135 and o2 == o1+0 and i in [9, 10]):
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i]-2.0 , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])
                else:
                    test_cases.append([rx, ry+lsy[i] ,  deg2rad(o1),  lf1, wl1, lr1, wr1,      rx+lsx[i] , ry+fac*ad+lsy[i] ,  deg2rad(o2),  lf1+lfs2[i] , wl1+wls2[i] , lr1+lrs2[i] , wr1+wrs2[i] ])

    '''
    test_cases.extend([
        (rx, ry+lsy[0] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[0] , ry+fac*ad+lsy[0] ,  o2,  lf1+lfs2[0] , wl1+wls2[0] , lr1+lrs2[0] , wr1+wrs2[0] ),    
        (rx, ry+lsy[1] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[1] , ry+fac*ad+lsy[1] ,  o2,  lf1+lfs2[1] , wl1+wls2[1] , lr1+lrs2[1] , wr1+wrs2[1] ),
        (rx, ry+lsy[2] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[2] , ry+fac*ad+lsy[2] ,  o2,  lf1+lfs2[2] , wl1+wls2[2] , lr1+lrs2[2] , wr1+wrs2[2] ),
        (rx, ry+lsy[3] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[3] , ry+fac*ad+lsy[3] ,  o2,  lf1+lfs2[3] , wl1+wls2[3] , lr1+lrs2[3] , wr1+wrs2[3] ),
        (rx, ry+lsy[4] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[4] , ry+fac*ad+lsy[4] ,  o2,  lf1+lfs2[4] , wl1+wls2[4] , lr1+lrs2[4] , wr1+wrs2[4] ),
        (rx, ry+lsy[5] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[5] , ry+fac*ad+lsy[5] ,  o2,  lf1+lfs2[5] , wl1+wls2[5] , lr1+lrs2[5] , wr1+wrs2[5] ),
        (rx, ry+lsy[6] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[6] , ry+fac*ad+lsy[6] ,  o2,  lf1+lfs2[6] , wl1+wls2[6] , lr1+lrs2[6] , wr1+wrs2[6] ),
        (rx, ry+lsy[7] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[7] , ry+fac*ad+lsy[7] ,  o2,  lf1+lfs2[7] , wl1+wls2[7] , lr1+lrs2[7] , wr1+wrs2[7] ),
        (rx, ry+lsy[8] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[8] , ry+fac*ad+lsy[8] ,  o2,  lf1+lfs2[8] , wl1+wls2[8] , lr1+lrs2[8] , wr1+wrs2[8] ),
        (rx, ry+lsy[9] ,  o1,  lf1, wl1, lr1, wr1,      rx+lsx[9] , ry+fac*ad+lsy[9] ,  o2,  lf1+lfs2[9] , wl1+wls2[9] , lr1+lrs2[9] , wr1+wrs2[9] ),
        (rx, ry+lsy[10],  o1,  lf1, wl1, lr1, wr1,      rx+lsx[10], ry+fac*ad+lsy[10],  o2,  lf1+lfs2[10], wl1+wls2[10], lr1+lrs2[10], wr1+wrs2[10])
    ])
    '''
    startId = 0
    stopId = len(test_cases)
    results = []
    for case in test_cases:
        result = is_overlap(*case)
        # result = overlap(*case)
        results.append((case, result))
 
    return results, stopId, startId, test_cases

def plot_all_rectangles(results, filename, stopId, startId):
    fig = go.Figure()

    for i, (test_case, result) in enumerate(results):
        if(i < startId):
            continue
        cx1, cy1, angle1, lf1, wl1, lr1, wr1, cx2, cy2, angle2, lf2, wl2, lr2, wr2 = test_case
        
        rect1 = create_rectangle(cx1, cy1, angle1, lf1, wl1, lr1, wr1)
        rect2 = create_rectangle(cx2, cy2, angle2, lf2, wl2, lr2, wr2)
        
        x1, y1 = rect1.exterior.xy
        x2, y2 = rect2.exterior.xy
        
        # Plot rectangles
        fig.add_trace(go.Scatter(x=list(y1), y=list(x1), fill='toself', name=f'R1T{i+1}'))
        fig.add_trace(go.Scatter(x=list(y2), y=list(x2), fill='toself', name=f'R2T{i+1}'))
        
        # Plot center points
        fig.add_trace(go.Scatter(x=[cy1], y=[cx1], mode='markers', marker=dict(size=10), name=f'r1cT{i+1}'))
        fig.add_trace(go.Scatter(x=[cy2], y=[cx2], mode='markers', marker=dict(size=10), name=f'r2cT{i+1}'))
        
        if(i == stopId):
            break
    fig.update_layout(
        title="Rectangle Overlap Test Cases",
        xaxis_title="Y Axis",
        yaxis_title="X Axis"
    )
    
    fig.write_html(filename)

if __name__ == "__main__":
    results, stopId, startId, test_cases = caller()
    # df = DataFrame(test_cases, columns=["cx1", "cy1", "o1", "lf1", "wl1", "lr1", "wr1", "cx2", "cy2", "o2", "lf2", "wl2", "lr2", "wr2"])
    # df.to_csv("results.csv")
    # exit()
    plot_all_rectangles(results, "all_rectangles_overlap.html", stopId, startId)
    for i, (test_case, result) in enumerate(results):
        if(i < startId):
            continue
        print(f"Test case {i+1}: {'Overlap' if result else 'No Overlap'}")
        if(i == stopId):
            break


'''
t = (
(2  , 4 , 0.00f, 1, 1, 1, 2, 03.00f, 4.00f, 0.00f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(2  , 10, 0.00f, 1, 1, 1, 2, 03.00f, 10.0f, 0.00f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(2  , 14, 0.00f, 1, 1, 1, 2, 03.00f, 14.0f, 0.00f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(2  , 18, 0.00f, 1, 1, 1, 2, 03.00f, 18.0f, 0.00f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(2  , 26, 0.00f, 1, 1, 1, 2, 03.00f, 26.0f, 0.00f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(2  , 38, 0.00f, 1, 1, 1, 2, 03.00f, 38.0f, 0.00f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(2  , 48, 0.00f, 1, 1, 1, 2, 03.00f, 48.0f, 0.00f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(2  , 54, 0.00f, 1, 1, 1, 2, 03.00f, 54.0f, 0.00f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(2  , 60, 0.00f, 1, 1, 1, 2, 05.00f, 60.0f, 0.00f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(2  , 66, 0.00f, 1, 1, 1, 2, 06.00f, 66.0f, 0.00f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(2  , 74, 0.00f, 1, 1, 1, 2, 07.00f, 74.0f, 0.00f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(14 , 4 , 0.00f, 1, 1, 1, 2, 015.0f, 5.00f, 0.00f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(14 , 10, 0.00f, 1, 1, 1, 2, 015.0f, 11.0f, 0.00f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(14 , 14, 0.00f, 1, 1, 1, 2, 015.0f, 15.0f, 0.00f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(14 , 18, 0.00f, 1, 1, 1, 2, 015.0f, 19.0f, 0.00f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(14 , 26, 0.00f, 1, 1, 1, 2, 015.0f, 27.0f, 0.00f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(14 , 38, 0.00f, 1, 1, 1, 2, 015.0f, 39.0f, 0.00f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(14 , 48, 0.00f, 1, 1, 1, 2, 015.0f, 49.0f, 0.00f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(14 , 54, 0.00f, 1, 1, 1, 2, 015.0f, 55.0f, 0.00f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(14 , 60, 0.00f, 1, 1, 1, 2, 017.0f, 61.0f, 0.00f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(14 , 66, 0.00f, 1, 1, 1, 2, 018.0f, 67.0f, 0.00f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(14 , 74, 0.00f, 1, 1, 1, 2, 019.0f, 75.0f, 0.00f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(26 , 4 , 0.00f, 1, 1, 1, 2, 027.0f, 3.00f, 0.00f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(26 , 10, 0.00f, 1, 1, 1, 2, 027.0f, 9.00f, 0.00f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(26 , 14, 0.00f, 1, 1, 1, 2, 027.0f, 13.0f, 0.00f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(26 , 18, 0.00f, 1, 1, 1, 2, 027.0f, 17.0f, 0.00f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(26 , 26, 0.00f, 1, 1, 1, 2, 027.0f, 25.0f, 0.00f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(26 , 38, 0.00f, 1, 1, 1, 2, 027.0f, 37.0f, 0.00f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(26 , 48, 0.00f, 1, 1, 1, 2, 027.0f, 47.0f, 0.00f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(26 , 54, 0.00f, 1, 1, 1, 2, 027.0f, 53.0f, 0.00f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(26 , 60, 0.00f, 1, 1, 1, 2, 029.0f, 59.0f, 0.00f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(26 , 66, 0.00f, 1, 1, 1, 2, 030.0f, 65.0f, 0.00f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(26 , 74, 0.00f, 1, 1, 1, 2, 031.0f, 73.0f, 0.00f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(48 , 4 , 0.00f, 1, 1, 1, 2, 047.0f, 4.00f, 0.00f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(48 , 10, 0.00f, 1, 1, 1, 2, 047.0f, 10.0f, 0.00f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(48 , 14, 0.00f, 1, 1, 1, 2, 047.0f, 14.0f, 0.00f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(48 , 18, 0.00f, 1, 1, 1, 2, 047.0f, 18.0f, 0.00f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(48 , 26, 0.00f, 1, 1, 1, 2, 047.0f, 26.0f, 0.00f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(48 , 38, 0.00f, 1, 1, 1, 2, 047.0f, 38.0f, 0.00f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(48 , 48, 0.00f, 1, 1, 1, 2, 047.0f, 48.0f, 0.00f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(48 , 54, 0.00f, 1, 1, 1, 2, 047.0f, 54.0f, 0.00f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(48 , 60, 0.00f, 1, 1, 1, 2, 045.0f, 60.0f, 0.00f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(48 , 66, 0.00f, 1, 1, 1, 2, 044.0f, 66.0f, 0.00f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(48 , 74, 0.00f, 1, 1, 1, 2, 043.0f, 74.0f, 0.00f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(60 , 4 , 3.14f, 1, 1, 1, 2, 061.0f, 4.00f, 3.14f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(60 , 10, 3.14f, 1, 1, 1, 2, 061.0f, 10.0f, 3.14f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(60 , 14, 3.14f, 1, 1, 1, 2, 061.0f, 14.0f, 3.14f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(60 , 18, 3.14f, 1, 1, 1, 2, 061.0f, 18.0f, 3.14f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(60 , 26, 3.14f, 1, 1, 1, 2, 061.0f, 26.0f, 3.14f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(60 , 38, 3.14f, 1, 1, 1, 2, 061.0f, 38.0f, 3.14f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(60 , 48, 3.14f, 1, 1, 1, 2, 061.0f, 48.0f, 3.14f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(60 , 54, 3.14f, 1, 1, 1, 2, 061.0f, 54.0f, 3.14f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(60 , 60, 3.14f, 1, 1, 1, 2, 063.0f, 60.0f, 3.14f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(60 , 66, 3.14f, 1, 1, 1, 2, 064.0f, 66.0f, 3.14f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(60 , 74, 3.14f, 1, 1, 1, 2, 065.0f, 74.0f, 3.14f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(72 , 4 , 3.14f, 1, 1, 1, 2, 073.0f, 4.00f, 2.97f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(72 , 10, 3.14f, 1, 1, 1, 2, 073.0f, 10.0f, 2.97f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(72 , 14, 3.14f, 1, 1, 1, 2, 073.0f, 14.0f, 2.97f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(72 , 18, 3.14f, 1, 1, 1, 2, 073.0f, 18.0f, 2.97f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(72 , 26, 3.14f, 1, 1, 1, 2, 073.0f, 26.0f, 2.97f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(72 , 38, 3.14f, 1, 1, 1, 2, 073.0f, 38.0f, 2.97f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(72 , 48, 3.14f, 1, 1, 1, 2, 073.0f, 48.0f, 2.97f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(72 , 54, 3.14f, 1, 1, 1, 2, 073.0f, 54.0f, 2.97f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(72 , 60, 3.14f, 1, 1, 1, 2, 075.0f, 60.0f, 2.97f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(72 , 66, 3.14f, 1, 1, 1, 2, 076.0f, 66.0f, 2.97f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(72 , 74, 3.14f, 1, 1, 1, 2, 077.0f, 74.0f, 2.97f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(84 , 4 , 3.14f, 1, 1, 1, 2, 085.0f, 4.00f, 2.79f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(84 , 10, 3.14f, 1, 1, 1, 2, 085.0f, 10.0f, 2.79f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(84 , 14, 3.14f, 1, 1, 1, 2, 085.0f, 14.0f, 2.79f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(84 , 18, 3.14f, 1, 1, 1, 2, 085.0f, 18.0f, 2.79f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(84 , 26, 3.14f, 1, 1, 1, 2, 085.0f, 26.0f, 2.79f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(84 , 38, 3.14f, 1, 1, 1, 2, 085.0f, 38.0f, 2.79f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(84 , 48, 3.14f, 1, 1, 1, 2, 085.0f, 48.0f, 2.79f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(84 , 54, 3.14f, 1, 1, 1, 2, 085.0f, 54.0f, 2.79f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(84 , 60, 3.14f, 1, 1, 1, 2, 087.0f, 60.0f, 2.79f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(84 , 66, 3.14f, 1, 1, 1, 2, 088.0f, 66.0f, 2.79f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(84 , 74, 3.14f, 1, 1, 1, 2, 089.0f, 74.0f, 2.79f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(96 , 4 , 3.14f, 1, 1, 1, 2, 097.0f, 4.00f, 2.62f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(96 , 10, 3.14f, 1, 1, 1, 2, 097.0f, 10.0f, 2.62f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(96 , 14, 3.14f, 1, 1, 1, 2, 097.0f, 14.0f, 2.62f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(96 , 18, 3.14f, 1, 1, 1, 2, 097.0f, 18.0f, 2.62f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(96 , 26, 3.14f, 1, 1, 1, 2, 097.0f, 26.0f, 2.62f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(96 , 38, 3.14f, 1, 1, 1, 2, 097.0f, 38.0f, 2.62f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(96 , 48, 3.14f, 1, 1, 1, 2, 097.0f, 48.0f, 2.62f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(96 , 54, 3.14f, 1, 1, 1, 2, 097.0f, 54.0f, 2.62f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(96 , 60, 3.14f, 1, 1, 1, 2, 099.0f, 60.0f, 2.62f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(96 , 66, 3.14f, 1, 1, 1, 2, 100.0f, 66.0f, 2.62f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(96 , 74, 3.14f, 1, 1, 1, 2, 100.0f, 74.0f, 2.62f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(108, 4 , 2.36f, 1, 1, 1, 2, 109.0f, 4.00f, 2.36f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(108, 10, 2.36f, 1, 1, 1, 2, 109.0f, 10.0f, 2.36f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(108, 14, 2.36f, 1, 1, 1, 2, 109.0f, 14.0f, 2.36f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(108, 18, 2.36f, 1, 1, 1, 2, 109.0f, 18.0f, 2.36f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(108, 26, 2.36f, 1, 1, 1, 2, 109.0f, 26.0f, 2.36f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(108, 38, 2.36f, 1, 1, 1, 2, 109.0f, 38.0f, 2.36f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(108, 48, 2.36f, 1, 1, 1, 2, 109.0f, 48.0f, 2.36f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(108, 54, 2.36f, 1, 1, 1, 2, 109.0f, 54.0f, 2.36f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(108, 60, 2.36f, 1, 1, 1, 2, 108.5f, 60.0f, 2.36f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(108, 66, 2.36f, 1, 1, 1, 2, 109.5f, 66.0f, 2.36f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(108, 74, 2.36f, 1, 1, 1, 2, 110.5f, 74.0f, 2.36f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(120, 4 , 2.36f, 1, 1, 1, 2, 121.0f, 4.00f, 2.18f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(120, 10, 2.36f, 1, 1, 1, 2, 121.0f, 10.0f, 2.18f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(120, 14, 2.36f, 1, 1, 1, 2, 121.0f, 14.0f, 2.18f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(120, 18, 2.36f, 1, 1, 1, 2, 121.0f, 18.0f, 2.18f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(120, 26, 2.36f, 1, 1, 1, 2, 121.0f, 26.0f, 2.18f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(120, 38, 2.36f, 1, 1, 1, 2, 121.0f, 38.0f, 2.18f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(120, 48, 2.36f, 1, 1, 1, 2, 121.0f, 48.0f, 2.18f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(120, 54, 2.36f, 1, 1, 1, 2, 121.0f, 54.0f, 2.18f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(120, 60, 2.36f, 1, 1, 1, 2, 120.3f, 60.0f, 2.18f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(120, 66, 2.36f, 1, 1, 1, 2, 121.3f, 66.0f, 2.18f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(120, 74, 2.36f, 1, 1, 1, 2, 122.3f, 74.0f, 2.18f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(132, 4 , 2.36f, 1, 1, 1, 2, 133.0f, 4.00f, 2.01f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(132, 10, 2.36f, 1, 1, 1, 2, 133.0f, 10.0f, 2.01f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(132, 14, 2.36f, 1, 1, 1, 2, 133.0f, 14.0f, 2.01f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(132, 18, 2.36f, 1, 1, 1, 2, 133.0f, 18.0f, 2.01f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(132, 26, 2.36f, 1, 1, 1, 2, 133.0f, 26.0f, 2.01f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(132, 38, 2.36f, 1, 1, 1, 2, 133.0f, 38.0f, 2.01f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(132, 48, 2.36f, 1, 1, 1, 2, 133.0f, 48.0f, 2.01f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(132, 54, 2.36f, 1, 1, 1, 2, 133.0f, 54.0f, 2.01f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(132, 60, 2.36f, 1, 1, 1, 2, 132.3f, 60.0f, 2.01f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(132, 66, 2.36f, 1, 1, 1, 2, 133.3f, 66.0f, 2.01f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(132, 74, 2.36f, 1, 1, 1, 2, 134.3f, 74.0f, 2.01f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(144, 4 , 2.36f, 1, 1, 1, 2, 145.0f, 4.00f, 1.83f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(144, 10, 2.36f, 1, 1, 1, 2, 145.0f, 10.0f, 1.83f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(144, 14, 2.36f, 1, 1, 1, 2, 145.0f, 14.0f, 1.83f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(144, 18, 2.36f, 1, 1, 1, 2, 145.0f, 18.0f, 1.83f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(144, 26, 2.36f, 1, 1, 1, 2, 145.0f, 26.0f, 1.83f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(144, 38, 2.36f, 1, 1, 1, 2, 145.0f, 38.0f, 1.83f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(144, 48, 2.36f, 1, 1, 1, 2, 145.0f, 48.0f, 1.83f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(144, 54, 2.36f, 1, 1, 1, 2, 145.0f, 54.0f, 1.83f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(144, 60, 2.36f, 1, 1, 1, 2, 144.3f, 60.0f, 1.83f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(144, 66, 2.36f, 1, 1, 1, 2, 145.3f, 66.0f, 1.83f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(144, 74, 2.36f, 1, 1, 1, 2, 146.3f, 74.0f, 1.83f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(156, 4 , 1.57f, 1, 1, 1, 2, 157.0f, 3.50f, 1.57f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(156, 10, 1.57f, 1, 1, 1, 2, 157.0f, 9.50f, 1.57f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(156, 14, 1.57f, 1, 1, 1, 2, 157.0f, 13.5f, 1.57f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(156, 18, 1.57f, 1, 1, 1, 2, 157.0f, 17.5f, 1.57f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(156, 26, 1.57f, 1, 1, 1, 2, 157.0f, 25.5f, 1.57f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(156, 38, 1.57f, 1, 1, 1, 2, 157.0f, 37.5f, 1.57f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(156, 48, 1.57f, 1, 1, 1, 2, 157.0f, 48.0f, 1.57f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(156, 54, 1.57f, 1, 1, 1, 2, 157.0f, 54.0f, 1.57f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(156, 60, 1.57f, 1, 1, 1, 2, 156.3f, 60.0f, 1.57f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(156, 66, 1.57f, 1, 1, 1, 2, 157.3f, 66.0f, 1.57f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(156, 74, 1.57f, 1, 1, 1, 2, 157.5f, 74.0f, 1.57f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(168, 4 , 1.57f, 1, 1, 1, 2, 169.0f, 4.00f, 1.40f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(168, 10, 1.57f, 1, 1, 1, 2, 169.0f, 10.0f, 1.40f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(168, 14, 1.57f, 1, 1, 1, 2, 169.0f, 14.0f, 1.40f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(168, 18, 1.57f, 1, 1, 1, 2, 169.0f, 18.0f, 1.40f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(168, 26, 1.57f, 1, 1, 1, 2, 169.0f, 26.0f, 1.40f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(168, 38, 1.57f, 1, 1, 1, 2, 169.0f, 38.0f, 1.40f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(168, 48, 1.57f, 1, 1, 1, 2, 169.0f, 48.0f, 1.40f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(168, 54, 1.57f, 1, 1, 1, 2, 169.0f, 54.0f, 1.40f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(168, 60, 1.57f, 1, 1, 1, 2, 168.0f, 60.0f, 1.40f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(168, 66, 1.57f, 1, 1, 1, 2, 169.0f, 66.0f, 1.40f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(168, 74, 1.57f, 1, 1, 1, 2, 170.0f, 74.0f, 1.40f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(180, 4 , 1.57f, 1, 1, 1, 2, 181.0f, 4.00f, 1.22f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(180, 10, 1.57f, 1, 1, 1, 2, 181.0f, 10.0f, 1.22f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(180, 14, 1.57f, 1, 1, 1, 2, 181.0f, 14.0f, 1.22f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(180, 18, 1.57f, 1, 1, 1, 2, 181.0f, 18.0f, 1.22f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(180, 26, 1.57f, 1, 1, 1, 2, 181.0f, 26.0f, 1.22f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(180, 38, 1.57f, 1, 1, 1, 2, 181.0f, 38.0f, 1.22f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(180, 48, 1.57f, 1, 1, 1, 2, 181.0f, 48.0f, 1.22f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(180, 54, 1.57f, 1, 1, 1, 2, 181.0f, 54.0f, 1.22f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(180, 60, 1.57f, 1, 1, 1, 2, 180.0f, 60.0f, 1.22f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(180, 66, 1.57f, 1, 1, 1, 2, 181.0f, 66.0f, 1.22f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(180, 74, 1.57f, 1, 1, 1, 2, 182.0f, 74.0f, 1.22f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(192, 4 , 1.57f, 1, 1, 1, 2, 193.0f, 4.00f, 1.05f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(192, 10, 1.57f, 1, 1, 1, 2, 193.0f, 10.0f, 1.05f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(192, 14, 1.57f, 1, 1, 1, 2, 193.0f, 14.0f, 1.05f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(192, 18, 1.57f, 1, 1, 1, 2, 193.0f, 18.0f, 1.05f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(192, 26, 1.57f, 1, 1, 1, 2, 193.0f, 26.0f, 1.05f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(192, 38, 1.57f, 1, 1, 1, 2, 193.0f, 38.0f, 1.05f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(192, 48, 1.57f, 1, 1, 1, 2, 193.0f, 48.0f, 1.05f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(192, 54, 1.57f, 1, 1, 1, 2, 193.0f, 54.0f, 1.05f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(192, 60, 1.57f, 1, 1, 1, 2, 192.0f, 60.0f, 1.05f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(192, 66, 1.57f, 1, 1, 1, 2, 193.0f, 66.0f, 1.05f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(192, 74, 1.57f, 1, 1, 1, 2, 194.0f, 74.0f, 1.05f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(204, 4 , 0.79f, 1, 1, 1, 2, 205.0f, 4.00f, 0.79f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(204, 10, 0.79f, 1, 1, 1, 2, 205.0f, 10.0f, 0.79f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(204, 14, 0.79f, 1, 1, 1, 2, 205.0f, 14.0f, 0.79f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(204, 18, 0.79f, 1, 1, 1, 2, 205.0f, 18.0f, 0.79f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(204, 26, 0.79f, 1, 1, 1, 2, 205.0f, 26.0f, 0.79f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(204, 38, 0.79f, 1, 1, 1, 2, 205.0f, 38.0f, 0.79f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(204, 48, 0.79f, 1, 1, 1, 2, 205.0f, 48.0f, 0.79f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(204, 54, 0.79f, 1, 1, 1, 2, 205.0f, 54.0f, 0.79f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(204, 60, 0.79f, 1, 1, 1, 2, 204.3f, 60.0f, 0.79f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(204, 66, 0.79f, 1, 1, 1, 2, 205.3f, 66.0f, 0.79f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(204, 74, 0.79f, 1, 1, 1, 2, 206.3f, 74.0f, 0.79f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(216, 4 , 0.79f, 1, 1, 1, 2, 217.0f, 4.00f, 0.61f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(216, 10, 0.79f, 1, 1, 1, 2, 217.0f, 10.0f, 0.61f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(216, 14, 0.79f, 1, 1, 1, 2, 217.0f, 14.0f, 0.61f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(216, 18, 0.79f, 1, 1, 1, 2, 217.0f, 18.0f, 0.61f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(216, 26, 0.79f, 1, 1, 1, 2, 217.0f, 26.0f, 0.61f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(216, 38, 0.79f, 1, 1, 1, 2, 217.0f, 38.0f, 0.61f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(216, 48, 0.79f, 1, 1, 1, 2, 217.0f, 48.0f, 0.61f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(216, 54, 0.79f, 1, 1, 1, 2, 217.0f, 54.0f, 0.61f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(216, 60, 0.79f, 1, 1, 1, 2, 216.3f, 60.0f, 0.61f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(216, 66, 0.79f, 1, 1, 1, 2, 217.3f, 66.0f, 0.61f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(216, 74, 0.79f, 1, 1, 1, 2, 218.3f, 74.0f, 0.61f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(228, 4 , 0.79f, 1, 1, 1, 2, 229.0f, 4.00f, 0.44f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(228, 10, 0.79f, 1, 1, 1, 2, 229.0f, 10.0f, 0.44f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(228, 14, 0.79f, 1, 1, 1, 2, 229.0f, 14.0f, 0.44f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(228, 18, 0.79f, 1, 1, 1, 2, 229.0f, 18.0f, 0.44f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(228, 26, 0.79f, 1, 1, 1, 2, 229.0f, 26.0f, 0.44f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(228, 38, 0.79f, 1, 1, 1, 2, 229.0f, 38.0f, 0.44f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(228, 48, 0.79f, 1, 1, 1, 2, 229.0f, 48.0f, 0.44f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(228, 54, 0.79f, 1, 1, 1, 2, 226.3f, 54.0f, 0.44f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(228, 60, 0.79f, 1, 1, 1, 2, 228.3f, 60.0f, 0.44f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(228, 66, 0.79f, 1, 1, 1, 2, 229.3f, 66.0f, 0.44f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(228, 74, 0.79f, 1, 1, 1, 2, 230.3f, 74.0f, 0.44f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(240, 4 , 0.79f, 1, 1, 1, 2, 241.0f, 4.00f, 0.26f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(240, 10, 0.79f, 1, 1, 1, 2, 241.0f, 10.0f, 0.26f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(240, 14, 0.79f, 1, 1, 1, 2, 241.0f, 14.0f, 0.26f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(240, 18, 0.79f, 1, 1, 1, 2, 241.0f, 18.0f, 0.26f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(240, 26, 0.79f, 1, 1, 1, 2, 241.0f, 26.0f, 0.26f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(240, 38, 0.79f, 1, 1, 1, 2, 241.0f, 38.0f, 0.26f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(240, 48, 0.79f, 1, 1, 1, 2, 241.0f, 48.0f, 0.26f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(240, 54, 0.79f, 1, 1, 1, 2, 240.0f, 54.0f, 0.26f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(240, 60, 0.79f, 1, 1, 1, 2, 240.3f, 60.0f, 0.26f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(240, 66, 0.79f, 1, 1, 1, 2, 241.3f, 66.0f, 0.26f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(240, 74, 0.79f, 1, 1, 1, 2, 242.3f, 74.0f, 0.26f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(252, 4 , 0.00f, 1, 1, 1, 2, 253.0f, 4.00f, 0.17f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(252, 10, 0.00f, 1, 1, 1, 2, 253.0f, 10.0f, 0.17f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(252, 14, 0.00f, 1, 1, 1, 2, 253.0f, 14.0f, 0.17f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(252, 18, 0.00f, 1, 1, 1, 2, 253.0f, 18.0f, 0.17f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(252, 26, 0.00f, 1, 1, 1, 2, 253.0f, 26.0f, 0.17f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(252, 38, 0.00f, 1, 1, 1, 2, 253.0f, 38.0f, 0.17f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(252, 48, 0.00f, 1, 1, 1, 2, 253.0f, 48.0f, 0.17f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(252, 54, 0.00f, 1, 1, 1, 2, 253.0f, 54.0f, 0.17f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(252, 60, 0.00f, 1, 1, 1, 2, 255.0f, 60.0f, 0.17f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(252, 66, 0.00f, 1, 1, 1, 2, 256.0f, 66.0f, 0.17f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(252, 74, 0.00f, 1, 1, 1, 2, 257.0f, 74.0f, 0.17f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(264, 4 , 0.00f, 1, 1, 1, 2, 265.0f, 4.00f, 0.35f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(264, 10, 0.00f, 1, 1, 1, 2, 265.0f, 10.0f, 0.35f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(264, 14, 0.00f, 1, 1, 1, 2, 265.0f, 14.0f, 0.35f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(264, 18, 0.00f, 1, 1, 1, 2, 265.0f, 18.0f, 0.35f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(264, 26, 0.00f, 1, 1, 1, 2, 265.0f, 26.0f, 0.35f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(264, 38, 0.00f, 1, 1, 1, 2, 265.0f, 38.0f, 0.35f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(264, 48, 0.00f, 1, 1, 1, 2, 265.0f, 48.0f, 0.35f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(264, 54, 0.00f, 1, 1, 1, 2, 265.0f, 54.0f, 0.35f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(264, 60, 0.00f, 1, 1, 1, 2, 267.0f, 60.0f, 0.35f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(264, 66, 0.00f, 1, 1, 1, 2, 268.0f, 66.0f, 0.35f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(264, 74, 0.00f, 1, 1, 1, 2, 269.0f, 74.0f, 0.35f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(276, 4 , 0.00f, 1, 1, 1, 2, 277.0f, 4.00f, 0.52f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(276, 10, 0.00f, 1, 1, 1, 2, 277.0f, 10.0f, 0.52f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(276, 14, 0.00f, 1, 1, 1, 2, 277.0f, 14.0f, 0.52f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(276, 18, 0.00f, 1, 1, 1, 2, 277.0f, 18.0f, 0.52f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(276, 26, 0.00f, 1, 1, 1, 2, 277.0f, 26.0f, 0.52f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(276, 38, 0.00f, 1, 1, 1, 2, 277.0f, 38.0f, 0.52f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(276, 48, 0.00f, 1, 1, 1, 2, 277.0f, 48.0f, 0.52f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(276, 54, 0.00f, 1, 1, 1, 2, 277.0f, 54.0f, 0.52f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(276, 60, 0.00f, 1, 1, 1, 2, 279.0f, 60.0f, 0.52f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(276, 66, 0.00f, 1, 1, 1, 2, 280.0f, 66.0f, 0.52f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(276, 74, 0.00f, 1, 1, 1, 2, 281.0f, 74.0f, 0.52f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(288, 4 , 0.79f, 1, 1, 1, 2, 289.0f, 4.00f, 0.79f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(288, 10, 0.79f, 1, 1, 1, 2, 289.0f, 10.0f, 0.79f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(288, 14, 0.79f, 1, 1, 1, 2, 289.0f, 14.0f, 0.79f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(288, 18, 0.79f, 1, 1, 1, 2, 289.0f, 18.0f, 0.79f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(288, 26, 0.79f, 1, 1, 1, 2, 289.0f, 26.0f, 0.79f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(288, 38, 0.79f, 1, 1, 1, 2, 289.0f, 38.0f, 0.79f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(288, 48, 0.79f, 1, 1, 1, 2, 289.0f, 48.0f, 0.79f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(288, 54, 0.79f, 1, 1, 1, 2, 289.0f, 54.0f, 0.79f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(288, 60, 0.79f, 1, 1, 1, 2, 291.0f, 60.0f, 0.79f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(288, 66, 0.79f, 1, 1, 1, 2, 290.5f, 66.0f, 0.79f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(288, 74, 0.79f, 1, 1, 1, 2, 291.5f, 74.0f, 0.79f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(300, 4 , 0.79f, 1, 1, 1, 2, 301.0f, 4.00f, 0.96f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(300, 10, 0.79f, 1, 1, 1, 2, 301.0f, 10.0f, 0.96f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(300, 14, 0.79f, 1, 1, 1, 2, 301.0f, 14.0f, 0.96f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(300, 18, 0.79f, 1, 1, 1, 2, 301.0f, 18.0f, 0.96f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(300, 26, 0.79f, 1, 1, 1, 2, 301.0f, 26.0f, 0.96f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(300, 38, 0.79f, 1, 1, 1, 2, 301.0f, 38.0f, 0.96f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(300, 48, 0.79f, 1, 1, 1, 2, 301.0f, 48.0f, 0.96f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(300, 54, 0.79f, 1, 1, 1, 2, 301.0f, 54.0f, 0.96f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(300, 60, 0.79f, 1, 1, 1, 2, 303.0f, 60.0f, 0.96f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(300, 66, 0.79f, 1, 1, 1, 2, 301.3f, 66.0f, 0.96f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(300, 74, 0.79f, 1, 1, 1, 2, 302.3f, 74.0f, 0.96f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(312, 4 , 0.79f, 1, 1, 1, 2, 313.0f, 4.00f, 1.13f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(312, 10, 0.79f, 1, 1, 1, 2, 313.0f, 10.0f, 1.13f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(312, 14, 0.79f, 1, 1, 1, 2, 313.0f, 14.0f, 1.13f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(312, 18, 0.79f, 1, 1, 1, 2, 313.0f, 18.0f, 1.13f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(312, 26, 0.79f, 1, 1, 1, 2, 313.0f, 26.0f, 1.13f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(312, 38, 0.79f, 1, 1, 1, 2, 313.0f, 38.0f, 1.13f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(312, 48, 0.79f, 1, 1, 1, 2, 313.0f, 48.0f, 1.13f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(312, 54, 0.79f, 1, 1, 1, 2, 313.0f, 54.0f, 1.13f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(312, 60, 0.79f, 1, 1, 1, 2, 315.0f, 60.0f, 1.13f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(312, 66, 0.79f, 1, 1, 1, 2, 313.3f, 66.0f, 1.13f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(312, 74, 0.79f, 1, 1, 1, 2, 314.3f, 74.0f, 1.13f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(324, 4 , 0.79f, 1, 1, 1, 2, 325.0f, 4.00f, 1.31f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(324, 10, 0.79f, 1, 1, 1, 2, 325.0f, 10.0f, 1.31f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(324, 14, 0.79f, 1, 1, 1, 2, 325.0f, 14.0f, 1.31f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(324, 18, 0.79f, 1, 1, 1, 2, 325.0f, 18.0f, 1.31f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(324, 26, 0.79f, 1, 1, 1, 2, 325.0f, 26.0f, 1.31f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(324, 38, 0.79f, 1, 1, 1, 2, 325.0f, 38.0f, 1.31f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(324, 48, 0.79f, 1, 1, 1, 2, 325.0f, 48.0f, 1.31f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(324, 54, 0.79f, 1, 1, 1, 2, 325.0f, 54.0f, 1.31f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(324, 60, 0.79f, 1, 1, 1, 2, 327.0f, 60.0f, 1.31f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(324, 66, 0.79f, 1, 1, 1, 2, 325.3f, 66.0f, 1.31f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(324, 74, 0.79f, 1, 1, 1, 2, 326.3f, 74.0f, 1.31f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(336, 4 , 1.57f, 1, 1, 1, 2, 337.0f, 3.50f, 1.57f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(336, 10, 1.57f, 1, 1, 1, 2, 337.0f, 9.50f, 1.57f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(336, 14, 1.57f, 1, 1, 1, 2, 337.0f, 13.5f, 1.57f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(336, 18, 1.57f, 1, 1, 1, 2, 337.0f, 17.5f, 1.57f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(336, 26, 1.57f, 1, 1, 1, 2, 337.0f, 25.5f, 1.57f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(336, 38, 1.57f, 1, 1, 1, 2, 337.0f, 37.5f, 1.57f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(336, 48, 1.57f, 1, 1, 1, 2, 337.0f, 48.0f, 1.57f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(336, 54, 1.57f, 1, 1, 1, 2, 337.0f, 54.0f, 1.57f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(336, 60, 1.57f, 1, 1, 1, 2, 338.3f, 60.0f, 1.57f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(336, 66, 1.57f, 1, 1, 1, 2, 337.3f, 66.0f, 1.57f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(336, 74, 1.57f, 1, 1, 1, 2, 338.3f, 74.0f, 1.57f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(348, 4 , 1.57f, 1, 1, 1, 2, 349.0f, 4.00f, 1.75f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(348, 10, 1.57f, 1, 1, 1, 2, 349.0f, 10.0f, 1.75f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(348, 14, 1.57f, 1, 1, 1, 2, 349.0f, 14.0f, 1.75f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(348, 18, 1.57f, 1, 1, 1, 2, 349.0f, 18.0f, 1.75f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(348, 26, 1.57f, 1, 1, 1, 2, 349.0f, 26.0f, 1.75f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(348, 38, 1.57f, 1, 1, 1, 2, 349.0f, 38.0f, 1.75f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(348, 48, 1.57f, 1, 1, 1, 2, 349.0f, 48.0f, 1.75f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(348, 54, 1.57f, 1, 1, 1, 2, 349.0f, 54.0f, 1.75f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(348, 60, 1.57f, 1, 1, 1, 2, 351.0f, 60.0f, 1.75f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(348, 66, 1.57f, 1, 1, 1, 2, 349.3f, 66.0f, 1.75f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(348, 74, 1.57f, 1, 1, 1, 2, 350.3f, 74.0f, 1.75f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(360, 4 , 1.57f, 1, 1, 1, 2, 361.0f, 4.00f, 1.92f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(360, 10, 1.57f, 1, 1, 1, 2, 361.0f, 10.0f, 1.92f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(360, 14, 1.57f, 1, 1, 1, 2, 361.0f, 14.0f, 1.92f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(360, 18, 1.57f, 1, 1, 1, 2, 361.0f, 18.0f, 1.92f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(360, 26, 1.57f, 1, 1, 1, 2, 361.0f, 26.0f, 1.92f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(360, 38, 1.57f, 1, 1, 1, 2, 361.0f, 38.0f, 1.92f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(360, 48, 1.57f, 1, 1, 1, 2, 361.0f, 48.0f, 1.92f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(360, 54, 1.57f, 1, 1, 1, 2, 361.0f, 54.0f, 1.92f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(360, 60, 1.57f, 1, 1, 1, 2, 363.0f, 60.0f, 1.92f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(360, 66, 1.57f, 1, 1, 1, 2, 361.3f, 66.0f, 1.92f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(360, 74, 1.57f, 1, 1, 1, 2, 362.3f, 74.0f, 1.92f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(372, 4 , 1.57f, 1, 1, 1, 2, 373.0f, 4.00f, 2.09f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(372, 10, 1.57f, 1, 1, 1, 2, 373.0f, 10.0f, 2.09f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(372, 14, 1.57f, 1, 1, 1, 2, 373.0f, 14.0f, 2.09f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(372, 18, 1.57f, 1, 1, 1, 2, 373.0f, 18.0f, 2.09f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(372, 26, 1.57f, 1, 1, 1, 2, 373.0f, 26.0f, 2.09f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(372, 38, 1.57f, 1, 1, 1, 2, 373.0f, 38.0f, 2.09f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(372, 48, 1.57f, 1, 1, 1, 2, 373.0f, 48.0f, 2.09f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(372, 54, 1.57f, 1, 1, 1, 2, 373.0f, 54.0f, 2.09f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(372, 60, 1.57f, 1, 1, 1, 2, 375.0f, 60.0f, 2.09f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(372, 66, 1.57f, 1, 1, 1, 2, 373.3f, 66.0f, 2.09f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(372, 74, 1.57f, 1, 1, 1, 2, 374.3f, 74.0f, 2.09f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(384, 4 , 2.36f, 1, 1, 1, 2, 385.0f, 4.00f, 2.36f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(384, 10, 2.36f, 1, 1, 1, 2, 385.0f, 10.0f, 2.36f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(384, 14, 2.36f, 1, 1, 1, 2, 385.0f, 14.0f, 2.36f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(384, 18, 2.36f, 1, 1, 1, 2, 385.0f, 18.0f, 2.36f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(384, 26, 2.36f, 1, 1, 1, 2, 385.0f, 26.0f, 2.36f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(384, 38, 2.36f, 1, 1, 1, 2, 385.0f, 38.0f, 2.36f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(384, 48, 2.36f, 1, 1, 1, 2, 385.0f, 48.0f, 2.36f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(384, 54, 2.36f, 1, 1, 1, 2, 385.0f, 54.0f, 2.36f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(384, 60, 2.36f, 1, 1, 1, 2, 387.0f, 60.0f, 2.36f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(384, 66, 2.36f, 1, 1, 1, 2, 386.0f, 66.0f, 2.36f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(384, 74, 2.36f, 1, 1, 1, 2, 387.0f, 74.0f, 2.36f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(396, 4 , 2.36f, 1, 1, 1, 2, 397.0f, 4.00f, 2.53f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(396, 10, 2.36f, 1, 1, 1, 2, 397.0f, 10.0f, 2.53f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(396, 14, 2.36f, 1, 1, 1, 2, 397.0f, 14.0f, 2.53f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(396, 18, 2.36f, 1, 1, 1, 2, 397.0f, 18.0f, 2.53f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(396, 26, 2.36f, 1, 1, 1, 2, 397.0f, 26.0f, 2.53f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(396, 38, 2.36f, 1, 1, 1, 2, 397.0f, 38.0f, 2.53f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(396, 48, 2.36f, 1, 1, 1, 2, 397.0f, 48.0f, 2.53f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(396, 54, 2.36f, 1, 1, 1, 2, 397.0f, 54.0f, 2.53f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(396, 60, 2.36f, 1, 1, 1, 2, 399.0f, 60.0f, 2.53f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(396, 66, 2.36f, 1, 1, 1, 2, 400.0f, 66.0f, 2.53f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(396, 74, 2.36f, 1, 1, 1, 2, 401.0f, 74.0f, 2.53f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(408, 4 , 2.36f, 1, 1, 1, 2, 409.0f, 4.00f, 2.71f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(408, 10, 2.36f, 1, 1, 1, 2, 409.0f, 10.0f, 2.71f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(408, 14, 2.36f, 1, 1, 1, 2, 409.0f, 14.0f, 2.71f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(408, 18, 2.36f, 1, 1, 1, 2, 409.0f, 18.0f, 2.71f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(408, 26, 2.36f, 1, 1, 1, 2, 409.0f, 26.0f, 2.71f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(408, 38, 2.36f, 1, 1, 1, 2, 409.0f, 38.0f, 2.71f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(408, 48, 2.36f, 1, 1, 1, 2, 409.0f, 48.0f, 2.71f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(408, 54, 2.36f, 1, 1, 1, 2, 409.0f, 54.0f, 2.71f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(408, 60, 2.36f, 1, 1, 1, 2, 411.0f, 60.0f, 2.71f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(408, 66, 2.36f, 1, 1, 1, 2, 412.0f, 66.0f, 2.71f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(408, 74, 2.36f, 1, 1, 1, 2, 413.0f, 74.0f, 2.71f, 5.0f, 1.00f, 5.00f, 1.00f, TYP),
(420, 4 , 2.36f, 1, 1, 1, 2, 421.0f, 4.00f, 2.88f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(420, 10, 2.36f, 1, 1, 1, 2, 421.0f, 10.0f, 2.88f, 1.0f, 0.50f, 1.00f, 2.00f, TYP),
(420, 14, 2.36f, 1, 1, 1, 2, 421.0f, 14.0f, 2.88f, 1.0f, 0.50f, 0.50f, 0.50f, TYP),
(420, 18, 2.36f, 1, 1, 1, 2, 421.0f, 18.0f, 2.88f, 1.0f, 0.50f, 0.30f, 0.30f, TYP),
(420, 26, 2.36f, 1, 1, 1, 2, 421.0f, 26.0f, 2.88f, 1.0f, 4.00f, 1.00f, 4.00f, TYP),
(420, 38, 2.36f, 1, 1, 1, 2, 421.0f, 38.0f, 2.88f, 1.0f, 5.00f, 1.00f, 5.00f, TYP),
(420, 48, 2.36f, 1, 1, 1, 2, 421.0f, 48.0f, 2.88f, 0.5f, 0.50f, 0.50f, 2.00f, TYP),
(420, 54, 2.36f, 1, 1, 1, 2, 421.0f, 54.0f, 2.88f, 0.2f, 0.50f, 0.20f, 2.00f, TYP),
(420, 60, 2.36f, 1, 1, 1, 2, 423.0f, 60.0f, 2.88f, 3.0f, 1.00f, 3.00f, 1.00f, TYP),
(420, 66, 2.36f, 1, 1, 1, 2, 424.0f, 66.0f, 2.88f, 4.0f, 1.00f, 4.00f, 1.00f, TYP),
(420, 74, 2.36f, 1, 1, 1, 2, 425.0f, 74.0f, 2.88f, 5.0f, 1.00f, 5.00f, 1.00f, TYP))
'''
