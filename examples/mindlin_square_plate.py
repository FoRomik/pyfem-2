#!/usr/bin/env python
# -*- coding: utf-8 -*-


if __name__ == "__main__":
    from mesh2d import rectangular_quads
    from mesh2d import draw_vtk
    from assembly2d import assembly_quads_mindlin_plate
    from assembly2d import assembly_initial_value
    from stress_strain_matrix import plane_stress_isotropic
    from force import volume_force_quads
    from scipy.sparse.linalg import spsolve
    from numpy import array

    a = 1.0 # A side of a square plate
    h = 0.01 # A thickness of a square plate
    e = 203200.0 # The Young's modulus
    nu = 0.3 # The Poisson's ratio
    q = 0.05 # A load intensity
    n = 201
    (nodes, elements) = rectangular_quads(x_count=n, y_count=n, x_origin=0.0, y_origin=0., width=a, height=a)

    stiffness = assembly_quads_mindlin_plate(nodes, elements, h, plane_stress_isotropic(e, nu))

    print("Evaluating force...")

    def force_func(node): return array([q, 0.0, 0.0])

    force = volume_force_quads(nodes=nodes, elements=elements, thickness=1.0, freedom=3, force_function=force_func, gauss_order=3)

    print("Evaluating boundary conditions...")
    for i in range(len(nodes)):
        if (abs(nodes[i, 0] - 0) < 0.0000001) or (abs(nodes[i, 0] - a) < 0.0000001) or (abs(nodes[i, 1] - 0) < 0.0000001) or (abs(nodes[i, 1] - a) < 0.0000001):
            assembly_initial_value(stiffness, force, 3 * i, 0.0)
            assembly_initial_value(stiffness, force, 3 * i + 1, 0.0)
            assembly_initial_value(stiffness, force, 3 * i + 2, 0.0)

    print("Solving a system of linear equations")

    x = spsolve(stiffness, force)

    w = x[0::3]
    theta_x = x[1::3]
    theta_y = x[2::3]
    print(min(w), " <= w <= ", max(w))
    print(min(theta_x), " <= theta x <= ", max(theta_x))
    print(min(theta_y), " <= theta y <= ", max(theta_y))
    print("Analytical bending: ", 0.00126 * q * a**4.0 * 12.0 * (1.0 - nu**2.0) / (e * h**3.0))
    draw_vtk(nodes, elements, w, title="w", show_labels=True)
    draw_vtk(nodes, elements, theta_x, title="theta x", show_labels=True)
    draw_vtk(nodes, elements, theta_y, title="theta y", show_labels=True)