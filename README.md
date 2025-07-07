# View_finder

A python based web app that takes a location and outputs the furthest visible point in any direction. 

How does it work>
- Viewfinder takes the location and draws lines eminating from that point in all directions. The density of the lines (lines/360 degrees) can be specified, with more lines resulting in higher resolution, but also longer processing time.
- Viewfinder then finds the elevation for each point along each line. The density of elevation points (elevation point/line) can be specified, with more points resulting in higher resolution but more processing time.
- Points are evaluated to be seen or not seen, based on the elevation compared to the initial location elevation, the angle between other points on the line, and the curvature of the earth.
- 
3d version
![image](https://github.com/user-attachments/assets/667e0a94-7efa-4c32-a582-a05e0da0a2a4)

![ezgif-1571a8d4228ebb](https://github.com/user-attachments/assets/4731d2fc-9a54-4feb-96bd-67bee69854c4)


2d version

![image](https://github.com/user-attachments/assets/44f6ba91-26ae-40ae-9353-6e009410a15b)
