#!/usr/bin/env python
# -*- coding: utf-8 -*-
from numpy import zeros
from numpy import array
from scipy.sparse import lil_matrix
from print_progress import print_progress


def assembly_quads_stress_strain(nodes, elements, thickness, elasticity_matrix, gauss_order=2):
    # type: (array, array, array, int) -> lil_matrix
    """
    Assembly Routine for the Plane Stress-Strain State Analysis using a Mesh of Quadrilaterals
    :param nodes: A two-dimensional array of coordinates (nodes)
    :param elements: A two-dimensional array of quads (a mesh)
    :param thickness: A thickness of an object
    :param elasticity_matrix: A two-dimensional array that represents stress-strain relations
    :param gauss_order: An order of gaussian quadratures (a count of points used to approximate in each direction)
    :return: A global stiffness matrix stored in the CSR sparse format
    Order: u_0, v0, u_1, v_1, ..., u_(n-1), v_(n-1); n is nodes count
    """
    from quadrature import legendre_quad
    from shape_functions import iso_quad
    print "The assembly routine is started."
    freedom = 2
    element_nodes = 4
    nodes_count = len(nodes)
    dimension = freedom * nodes_count
    element_dimension = freedom * element_nodes
    global_matrix = lil_matrix((dimension, dimension))
    elements_count = len(elements)
    (xi, eta, w) = legendre_quad(gauss_order)
    for element_index in range(elements_count):
        local = zeros((element_dimension, element_dimension))
        element = nodes[elements[element_index, :], :]
        for i in range(len(w)):
            (jacobian, shape, shape_dx, shape_dy) = iso_quad(element, xi[i], eta[i])
            b = array([
                [shape_dx[0],   0.0,            shape_dx[1],    0.0,            shape_dx[2],    0.0,            shape_dx[3],    0.0],
                [0.0,           shape_dy[0],    0.0,            shape_dy[1],    0.0,            shape_dy[2],    0.0,            shape_dy[3]],
                [shape_dy[0],   shape_dx[0],    shape_dy[1],    shape_dx[1],    shape_dy[2],    shape_dx[2],    shape_dy[3],    shape_dx[3]]
            ])
            bt = b.conj().transpose()
            local = local + thickness * bt.dot(elasticity_matrix).dot(b) * jacobian * w[i]
        for i in range(element_dimension):
            ii = elements[element_index, i / freedom] * freedom + i % freedom
            for j in range(i, element_dimension):
                jj = elements[element_index, j / freedom] * freedom + j % freedom
                global_matrix[ii, jj] += local[i, j]
                if i != j:
                    global_matrix[jj, ii] = global_matrix[ii, jj]
        print_progress(element_index, elements_count - 1)
    print "\nThe assembly routine is completed."
    return global_matrix.tocsr()


def assembly_triangles_stress_strain(nodes, elements, elasticity_matrix, gauss_order=2):
    # type: (array, array, array, int) -> lil_matrix
    """
    Assembly Routine for the Plane Stress-Strain State Analysis using a Mesh of Triangles
    :param nodes: A two-dimensional array of coordinates (nodes)
    :param elements: A two-dimensional array of quads (a mesh)
    :param elasticity_matrix: A two-dimensional array that represents stress-strain relations
    :param gauss_order: An order of gaussian quadratures (a count of points used to approximate in each direction)
    :return: A global stiffness matrix stored in the CSR sparse format
    Order: u_0, v0, u_1, v_1, ..., u_(n-1), v_(n-1); n is nodes count
    """
    from quadrature import legendre_triangle
    from shape_functions import iso_triangle
    print "The assembly routine is started."
    freedom = 2
    element_nodes = 3
    nodes_count = len(nodes)
    dimension = freedom * nodes_count
    element_dimension = freedom * element_nodes
    global_matrix = lil_matrix((dimension, dimension))
    elements_count = len(elements)
    (xi, eta, w) = legendre_triangle(gauss_order)
    for element_index in range(elements_count):
        local = zeros((element_dimension, element_dimension))
        element = nodes[elements[element_index, :], :]
        for i in range(len(w)):
            (jacobian, shape, shape_dx, shape_dy) = iso_triangle(element, xi[i], eta[i])
            b = array([
                [shape_dx[0],   0.0,            shape_dx[1],    0.0,            shape_dx[2],    0.0        ],
                [0.0,           shape_dy[0],    0.0,            shape_dy[1],    0.0,            shape_dy[2]],
                [shape_dy[0],   shape_dx[0],    shape_dy[1],    shape_dx[1],    shape_dy[2],    shape_dx[2]]
            ])
            bt = b.conj().transpose()
            local = local + bt.dot(elasticity_matrix).dot(b) * jacobian * w[i]
        for i in range(element_dimension):
            ii = elements[element_index, i / freedom] * freedom + i % freedom
            for j in range(i, element_dimension):
                jj = elements[element_index, j / freedom] * freedom + j % freedom
                global_matrix[ii, jj] += local[i, j]
                if i != j:
                    global_matrix[jj, ii] = global_matrix[ii, jj]
        print_progress(element_index, elements_count - 1)
    print "\nThe assembly routine is completed"
    return global_matrix.tocsr()


def assembly_quads_mindlin_plate(nodes, elements, thickness, elasticity_matrix, gauss_order=3, kappa=5.0/6.0):
    # type: (array, array, float, float, float, int, float) -> lil_matrix
    """
    Assembly Routine for the Mindlin Plates Analysis
    :param nodes: A two-dimensional array of plate's nodes coordinates
    :param elements: A two-dimensional array of plate's triangles (mesh)
    :param thickness: A thickness of a plate
    :param elasticity_matrix: A two-dimensional array that represents stress-strain relations
    :param gauss_order: An order of gaussian quadratures
    :param kappa: The shear correction factor
    :return: Global stiffness matrix in the CSR sparse format
    Order: u_0, v0, u_1, v_1, ..., u_(n-1), v_(n-1); n - nodes count
    """
    from quadrature import legendre_quad
    from shape_functions import iso_quad

    print "The assembly routine is started"
    freedom = 3
    element_nodes = 4
    nodes_count = len(nodes)
    dimension = freedom * nodes_count
    element_dimension = freedom * element_nodes
    global_matrix = lil_matrix((dimension, dimension))
    elements_count = len(elements)
    (xi, eta, w) = legendre_quad(gauss_order)
    df = elasticity_matrix
    dc = array([
        [df[2, 2], 0.0],
        [0.0, df[2, 2]]
    ])
    for element_index in range(elements_count):
        local = zeros((element_dimension, element_dimension))
        element = nodes[elements[element_index, :], :]
        for i in range(len(w)):
            (jacobian, shape, shape_dx, shape_dy) = iso_quad(element, xi[i], eta[i])
            bf = array([
                [0.0, shape_dx[0], 0.0,         0.0, shape_dx[1], 0.0,         0.0, shape_dx[2], 0.0,         0.0, shape_dx[3], 0.0],
                [0.0, 0.0,         shape_dy[0], 0.0, 0.0,         shape_dy[1], 0.0, 0.0,         shape_dy[2], 0.0, 0.0,         shape_dy[3]],
                [0.0, shape_dy[0], shape_dx[0], 0.0, shape_dy[1], shape_dx[1], 0.0, shape_dy[2], shape_dx[2], 0.0, shape_dy[3], shape_dx[3]]
            ])
            bc = array([
                [shape_dx[0], shape[0], 0.0, shape_dx[1], shape[1], 0.0, shape_dx[2], shape[2], 0.0, shape_dx[3], shape[3], 0.0],
                [shape_dy[0], 0.0, shape[0], shape_dy[1], 0.0, shape[1], shape_dy[2], 0.0, shape[2], shape_dy[3], 0.0, shape[3]]
            ])
            local = local + (thickness**3.0 / 12.0 * (bf.transpose().dot(df).dot(bf)) + kappa * thickness * (bc.transpose().dot(dc).dot(bc))) * jacobian * w[i]
        for i in range(element_dimension):
            ii = elements[element_index, i / freedom] * freedom + i % freedom
            for j in range(i, element_dimension):
                jj = elements[element_index, j / freedom] * freedom + j % freedom
                global_matrix[ii, jj] += local[i, j]
                if i != j:
                    global_matrix[jj, ii] = global_matrix[ii, jj]
        print_progress(element_index, elements_count - 1)
    print "\nThe assembly routine is completed"
    return global_matrix.tocsr()


def assembly_quads_mindlin_plate_laminated(nodes, elements, thicknesses, elasticity_matrices, gauss_order=3, kappa=5.0 / 6.0):
    # type: (array, array, float, float, float, int, float) -> lil_matrix
    """
    Assembly Routine for the Mindlin Plates Analysis
    :param nodes: A two-dimensional array of plate's nodes coordinates
    :param elements: A two-dimensional array of plate's triangles (mesh)
    :param thicknesses: An array of thicknesses that stores thicknesses of each layer
    :param elasticity_matrices: A list or a sequence of two-dimensional arrays. Each array represents stress-strain relations of corresponded layer
    :param gauss_order: An order of gaussian quadratures
    :param kappa: The shear correction factor
    :return: Global stiffness matrix in the CSR sparse format
    Order: u_0, v0, u_1, v_1, ..., u_(n-1), v_(n-1); n - nodes count
    """
    from quadrature import legendre_quad
    from shape_functions import iso_quad
    from numpy import sum

    print "The assembly routine is started"
    freedom = 5
    element_nodes = 4
    nodes_count = len(nodes)
    dimension = freedom * nodes_count
    element_dimension = freedom * element_nodes
    global_matrix = lil_matrix((dimension, dimension))
    elements_count = len(elements)
    (xi, eta, w) = legendre_quad(gauss_order)

    h = sum(thicknesses)

    for element_index in range(elements_count):
        local = zeros((element_dimension, element_dimension))
        element = nodes[elements[element_index, :], :]
        for i in range(len(w)):
            (jacobian, shape, shape_dx, shape_dy) = iso_quad(element, xi[i], eta[i])
            bm = array([
                [shape_dx[0], 0.0,         0.0, 0.0, 0.0, shape_dx[1], 0.0,         0.0, 0.0, 0.0, shape_dx[2], 0.0,         0.0, 0.0, 0.0, shape_dx[3], 0.0,         0.0, 0.0, 0.0],
                [0.0,         shape_dy[0], 0.0, 0.0, 0.0, 0.0,         shape_dy[1], 0.0, 0.0, 0.0, 0.0,         shape_dy[2], 0.0, 0.0, 0.0, 0.0,         shape_dy[3], 0.0, 0.0, 0.0],
                [shape_dy[0], shape_dx[0], 0.0, 0.0, 0.0, shape_dy[1], shape_dx[1], 0.0, 0.0, 0.0, shape_dy[2], shape_dx[2], 0.0, 0.0, 0.0, shape_dy[3], shape_dx[3], 0.0, 0.0, 0.0]
            ])
            bf = array([
                [0.0, 0.0, 0.0, shape_dx[0], 0.0,         0.0, 0.0, 0.0, shape_dx[1], 0.0,         0.0, 0.0, 0.0, shape_dx[2], 0.0,         0.0, 0.0, 0.0, shape_dx[3], 0.0],
                [0.0, 0.0, 0.0, 0.0,         shape_dy[0], 0.0, 0.0, 0.0, 0.0,         shape_dy[1], 0.0, 0.0, 0.0, 0.0,         shape_dy[2], 0.0, 0.0, 0.0, 0.0,         shape_dy[3]],
                [0.0, 0.0, 0.0, shape_dy[0], shape_dx[0], 0.0, 0.0, 0.0, shape_dy[1], shape_dx[1], 0.0, 0.0, 0.0, shape_dy[2], shape_dx[2], 0.0, 0.0, 0.0, shape_dy[3], shape_dx[3]]
            ])
            bc = array([
                [0.0, 0.0, shape_dx[0], shape[0], 0.0, 0.0, 0.0, shape_dx[1], shape[1], 0.0, 0.0, 0.0, shape_dx[2], shape[2], 0.0, 0.0, 0.0, shape_dx[3], shape[3], 0.0],
                [0.0, 0.0, shape_dy[0], 0.0, shape[0], 0.0, 0.0, shape_dy[1], 0.0, shape[1], 0.0, 0.0, shape_dy[2], 0.0, shape[2], 0.0, 0.0, shape_dy[3], 0.0, shape[3]]
            ])
            z0 = -h / 2.0
            for j in range(len(thicknesses)):
                z1 = z0 + thicknesses[j]
                df = elasticity_matrices[j]
                dc = array([
                    [df[2, 2], 0.0],
                    [0.0, df[2, 2]]
                ])
                local = local + (z1 - z0) * (bm.transpose().dot(df).dot(bm)) * jacobian * w[i]
                local = local + (z1**2.0 - z0**2.0) / 2.0 * (bm.transpose().dot(df).dot(bf)) * jacobian * w[i]
                local = local + (z1**2.0 - z0**2.0) / 2.0 * (bf.transpose().dot(df).dot(bm)) * jacobian * w[i]
                local = local + (z1**3.0 - z0**3.0) / 3.0 * (bf.transpose().dot(df).dot(bf)) * jacobian * w[i]
                local = local + (z1 - z0) * kappa * (bc.transpose().dot(dc).dot(bc)) * jacobian * w[i]
                z0 = z1

        for i in range(element_dimension):
            ii = elements[element_index, i / freedom] * freedom + i % freedom
            for j in range(i, element_dimension):
                jj = elements[element_index, j / freedom] * freedom + j % freedom
                global_matrix[ii, jj] += local[i, j]
                if i != j:
                    global_matrix[jj, ii] = global_matrix[ii, jj]
        print_progress(element_index, elements_count - 1)
    print "\nThe assembly routine is completed"
    return global_matrix.tocsr()


def assembly_quads_mindlin_plate_geometric(nodes, elements, thickness, sigma_x, sigma_y, tau_xy, gauss_order=3):
    from quadrature import legendre_quad
    from shape_functions import iso_quad
    from numpy import sum
    print "The assembly routine is started"
    freedom = 3
    element_nodes = 4
    nodes_count = len(nodes)
    dimension = freedom * nodes_count
    element_dimension = freedom * element_nodes
    geometric = lil_matrix((dimension, dimension))
    elements_count = len(elements)
    (xi, eta, w) = legendre_quad(gauss_order)

    for element_index in range(elements_count):
        kg = zeros((element_dimension, element_dimension))
        vertices = nodes[elements[element_index, :], :]
        sx = sigma_x[elements[element_index, :]]
        sy = sigma_y[elements[element_index, :]]
        txy = tau_xy[elements[element_index, :]]
        for i in range(len(w)):
            (jacobian, shape, shape_dx, shape_dy) = iso_quad(vertices, xi[i], eta[i])
            s0 = array([
                [sum(shape * sx), sum(shape * txy)],
                [sum(shape * txy), sum(shape * sy)]
            ])
            bb = array([
                [shape_dx[0], 0.0, 0.0, shape_dx[1], 0.0, 0.0, shape_dx[2], 0.0, 0.0, shape_dx[3], 0.0, 0.0],
                [shape_dy[0], 0.0, 0.0, shape_dy[1], 0.0, 0.0, shape_dy[2], 0.0, 0.0, shape_dy[3], 0.0, 0.0]
            ])
            bs1 = array([
                [0.0, shape_dx[0], 0.0, 0.0, shape_dx[1], 0.0, 0.0, shape_dx[2], 0.0, 0.0, shape_dx[3], 0.0],
                [0.0, shape_dy[0], 0.0, 0.0, shape_dy[1], 0.0, 0.0, shape_dy[2], 0.0, 0.0, shape_dy[3], 0.0]
            ])
            bs2 = array([
                [0.0, 0.0, shape_dx[0], 0.0, 0.0, shape_dx[1], 0.0, 0.0, shape_dx[2], 0.0, 0.0, shape_dx[3]],
                [0.0, 0.0, shape_dy[0], 0.0, 0.0, shape_dy[1], 0.0, 0.0, shape_dy[2], 0.0, 0.0, shape_dy[3]]
            ])
            kg = kg + thickness * bb.transpose().dot(s0).dot(bb) * jacobian * w[i] + thickness ** 3.0 / 12.0 * (
            bs1.transpose().dot(s0).dot(bs1) + bs2.transpose().dot(s0).dot(bs2)) * jacobian * w[i]

        for i in range(element_dimension):
            ii = elements[element_index, i / freedom] * freedom + i % freedom
            for j in range(i, element_dimension):
                jj = elements[element_index, j / freedom] * freedom + j % freedom
                geometric[ii, jj] += kg[i, j]
                if ii != jj:
                    geometric[jj, ii] = geometric[ii, jj]
        print_progress(element_index, elements_count - 1)
    print "\nThe assembly routine is completed"
    return geometric.tocsr()


def plate_stresses(nodes, elements, elasticity_matrix, displacement, z=0.0):
    from shape_functions import iso_quad, iso_triangle
    from math import sqrt
    freedom = 3
    element_nodes = len(elements[0, :])
    nodes_count = len(nodes)
    dimension = freedom * nodes_count
    element_dimension = freedom * element_nodes
    df = elasticity_matrix
    dc = array([
        [df[2, 2], 0.0],
        [0.0, df[2, 2]]
    ])
    xi =  array([-1.0, 1.0, 1.0, -1.0]) if element_nodes == 4 else array([0.0, 1.0, 0.0])
    eta = array([-1.0, -1.0, 1.0, 1.0]) if element_nodes == 4 else array([0.0, 0.0, 1.0])
    sigma_x = zeros(nodes_count)
    sigma_y = zeros(nodes_count)
    tau_xy = zeros(nodes_count)
    tau_xz = zeros(nodes_count)
    tau_yz = zeros(nodes_count)
    mises = zeros(nodes_count)
    adjacent = zeros(nodes_count)
    print("Recovering stresses")
    for element in elements:
        vertices = nodes[element[:], :]
        el_displ = zeros(element_nodes * freedom)
        for i in range(freedom):
            el_displ[i::freedom] = displacement[element[:] * freedom + i]

        for i in range(element_nodes):
            if element_nodes == 4:
                (jacobian, shape, shape_dx, shape_dy) = iso_quad(vertices, xi[i], eta[i])
            else:
                (jacobian, shape, shape_dx, shape_dy) = iso_triangle(vertices, xi[i], eta[i])

            bf = zeros((3, freedom * element_nodes))
            bc = zeros((2, freedom * element_nodes))
            for j in range(element_nodes):
                bf[0, j * freedom + 1] = shape_dx[j]
                bf[1, j * freedom + 2] = shape_dy[j]
                bf[2, j * freedom + 1] = shape_dy[j]
                bf[2, j * freedom + 2] = shape_dx[j]
                bc[0, j * freedom] = shape_dx[j]
                bc[0, j * freedom + 1] = shape[j]
                bc[1, j * freedom] = shape_dy[j]
                bc[1, j * freedom + 2] = shape[j]

            sigma = z * df.dot(bf).dot(el_displ)
            tau = dc.dot(bc).dot(el_displ)
            sigma_x[element[i]] += sigma[0]  #11
            sigma_y[element[i]] += sigma[1]  #22
            tau_xy[element[i]] += sigma[2]   # 12 21
            tau_xz[element[i]] += tau[0]  # 31 13
            tau_yz[element[i]] += tau[1]  # 23 32
            mises[element[i]] += sqrt(0.5 * ((sigma[0] - sigma[1])**2.0 + sigma[1]**2.0 + sigma[0]**2.0 + 6.0 * (sigma[2]**2.0 + tau[0]**2.0 + tau[1]**2.0)))
            adjacent[element[i]] += 1.0

    sigma_x /= adjacent
    sigma_y /= adjacent
    tau_xy /= adjacent
    tau_xz /= adjacent
    tau_yz /= adjacent
    mises /= adjacent
    return sigma_x, sigma_y, tau_xy, tau_xz, tau_yz, mises



def assembly_initial_value(stiffness, force, position, value=0.0):
    """
    Assembly routine modifies a linear system of equations. Unknown variable at the specified position will be equal to 
    the specified value 
    :param stiffness: A global matrix (mutable data type) of format CSR
    :param force: A column-vector (mutable data type)
    :param position: Number of unknown variable at the linear system  
    :param value: A value which variable at specified position must be equal
    :return: None
    """
    from scipy.sparse import  csr_matrix
    if not isinstance(stiffness, csr_matrix):
        raise ValueError('Stiffness matrix given must be of CSR format.')
    stiffness.data[stiffness.indptr[position]:stiffness.indptr[position + 1]] = 0.0
    # dimension = stiffness.shape[0]
    # for j in range(dimension):
    #     if j != position:
    #         force[j] -= stiffness[position, j] * value
    # for j in range(dimension):
    #     if stiffness[position, j] != 0.0:
    #         stiffness[position, j] = 0.0
    #     if stiffness[j, position] != 0.0:
    #         stiffness[j, position] = 0.0
    stiffness[position, position] = 1.0
    force[position] = value


if __name__ == "__main__":
    from mesh2d import rectangular_quads
    from mesh2d import rectangular_triangles
    from plot_coo_matrix import plot_coo_matrix
    d = array([
        [1., 1., 0.],
        [1., 1., 0.],
        [0., 0., 1.]
    ])
    (nodes, elements) = rectangular_quads(x_count=51, y_count=11, x_origin=-10.0, y_origin=-2.0, width=20.0, height=4.0)
    global_matrix = assembly_quads_stress_strain(nodes, elements, d)
    plot_coo_matrix(global_matrix)
    (nodes, elements) = rectangular_triangles(x_count=51, y_count=11, x_origin=-10.0, y_origin=-2.0, width=20.0, height=4.0)
    global_matrix = assembly_triangles_stress_strain(nodes, elements, d)
    plot_coo_matrix(global_matrix)
    (nodes, elements) = rectangular_quads(x_count=31, y_count=31, x_origin=0.0, y_origin=0, width=1, height=1)
    global_matrix = assembly_quads_mindlin_plate(nodes, elements, 0.1, 10920, 0.3)
    plot_coo_matrix(global_matrix)