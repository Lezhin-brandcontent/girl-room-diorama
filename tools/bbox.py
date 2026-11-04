import bpy, mathutils
groups={}
for ob in bpy.data.objects:
    if ob.type!='MESH': continue
    r=ob
    while r.parent: r=r.parent
    if r.name in ('room',): continue
    dg=bpy.context.evaluated_depsgraph_get()
    for c in ob.bound_box:
        w=ob.matrix_world@mathutils.Vector(c)
        g=groups.setdefault(r.name,[9,9,9,-9,-9,-9])
        for i in range(3):
            g[i]=min(g[i],w[i]); g[i+3]=max(g[i+3],w[i])
for k,g in sorted(groups.items()):
    print(f"BB {k:16s} x[{g[0]:.2f},{g[3]:.2f}] y[{g[1]:.2f},{g[4]:.2f}] z[{g[2]:.2f},{g[5]:.2f}]")
