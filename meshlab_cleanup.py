# %%

import pymeshlab
import numpy as np
import time #temp for diagnosis

def make_watertight(meshset, ambient_occlusion = True, fix_zero_area_faces = True):
    '''
    Makes a mesh watertight.
    First fixes non-manifold edges, or deleted the vertices.
    Then fixes  non-manifold vertices, or deletes the vertices.
    Then closes hole.
    returns the number of vertices removed.
    In many cases holes cannot be closed. 
    '''
    initial_verts = meshset.current_mesh().vertex_number() 
    #I was merging close vertices and removing null faces, which caused problems in that it creates zero area holes, which are hard to fix. 

    # meshset.turn_into_a_pure_triangular_mesh() 
    meshset.remove_duplicate_vertices()
    meshset.remove_duplicate_faces() 
    meshset.merge_close_vertices()
    meshset.remove_unreferenced_vertices()
    meshset.current_mesh().compact()
    print_checks(meshset)#for debugging
    meshset = fix_non_manifold(meshset)

    #####I MAY WANT TO CHANGE THIS TO VOLUMETRIC OBSCURANCE#####
    if ambient_occlusion:
        print('Removing vertices through ambient occlusion')
        try:
            meshset = vertex_removal_ambient_occlusion(meshset)
            meshset.close_holes(maxholesize = 150, selfintersection = False, newfaceselected = False)
            meshset = fix_non_manifold(meshset)
        except:
            print('Ambient occlusion removal failed')

    if fix_zero_area_faces:
        print('fixing zero area faces')
        while True:
            if zero_area_face_number(meshset) > 0:
                #Failing here sometimes? Need a try block?864691136084203884 fails
                #864691136084203884 would work prior to ambient occlusion
                #crashes the whole kernel
                #Works if I do it in ipython calling one at a time?
                #Is it a memory thing, and if I go slow enough it doesn't crash?
                print('Fixing zero faces by edge flipping')
                meshset.remove_t_vertices_by_edge_flip()
                print('Fixing non-manifold')
                meshset = fix_non_manifold(meshset)
                print_checks(meshset)#for debugging
                if zero_area_face_number(meshset) > 0:
                    print('Fixing zero faces by edge collapse')
                    meshset.remove_t_vertices_by_edge_collapse()
                    print_checks(meshset)#for debugging
                    meshset = fix_non_manifold(meshset)

                    if zero_area_face_number(meshset) > 0:
                        print('Fixing zero faces by isotropic explicit remeshing')
                        meshset.remove_zero_area_faces()
                        meshset.select_none()
                        meshset.select_border()
                        meshset.dilate_selection()
                        meshset.dilate_selection()
                        meshset = fix_non_manifold(meshset)

                        if zero_area_face_number(meshset) > 0:
                            print('Fixing zero faces vertex deletion')
                            meshset.remove_zero_area_faces()
                            meshset.select_none()
                            meshset.select_border()
                            meshset.delete_selected_vertices()
                            meshset = fix_non_manifold(meshset)

            meshset = delete_small_disconnected_component(meshset)
            if zero_area_face_number(meshset) == 0:
                ('Successfully repaired zero area faces')
                break
    meshset.current_mesh().compact()
    print('Finished make_watertight')
    return initial_verts - meshset.current_mesh().vertex_number()

def delete_small_disconnected_component(meshset):
    meshset.select_small_disconnected_component()
    meshset.select_vertices_from_faces()
    meshset.delete_selected_faces()
    meshset.delete_selected_vertices()
    meshset.remove_unreferenced_vertices()
    return meshset

def vertex_removal_ambient_occlusion(meshset):
    meshset.current_mesh().compact()
    meshset.select_none()
    meshset.ambient_occlusion(reqviews = 1024, usegpu = True, coneangle = 1024)
    vertex_quality_array = meshset.current_mesh().vertex_quality_array()
    min_quality = np.min(vertex_quality_array)
    if min_quality < 0.005:
        meshset.select_by_vertex_quality(minq = min_quality, maxq = 0.005, inclusive = False)
        print(f'Removing {meshset.current_mesh().selected_vertex_number()} vertices in vertex_removal_ambient_occlusion')
        meshset.delete_selected_faces()
        meshset.delete_selected_vertices()
        meshset = delete_small_disconnected_component(meshset)
        meshset.current_mesh().compact()
    else:
        print('No vertices to remove in vertex_removal_ambient_occlusion')
    return meshset

def is_2_manifold(meshset):
    meshset.select_non_manifold_edges_()
    if meshset.current_mesh().selected_vertex_number() != 0:
        return False
    meshset.select_non_manifold_vertices()
    if meshset.current_mesh().selected_vertex_number() != 0:
        return False
    return True

def zero_area_face_number(meshset):
    meshset.current_mesh().compact()
    meshset.select_none()
    meshset.per_face_quality_according_to_triangle_shape_and_aspect_ratio(metric = 'Area')
    face_quality = meshset.current_mesh().face_quality_array()#returns numpy array
    num_zero_area = face_quality.size - np.count_nonzero(face_quality)
    return num_zero_area

def self_intersecting_face_number(meshset):
    meshset.current_mesh().compact()
    meshset.select_none()
    meshset.select_self_intersecting_faces()
    return meshset.current_mesh().selected_face_number()

def problematic_face_number(meshset):
    meshset.current_mesh().compact()
    meshset.select_none()
    meshset.select_problematic_faces()
    return meshset.current_mesh().selected_face_number()

def border_vertex_number(meshset):
    meshset.current_mesh().compact()
    meshset.select_none()
    meshset.select_border()
    return meshset.current_mesh().selected_vertex_number()

def fix_non_manifold(meshset):
    if not is_2_manifold(meshset):
        print('Mesh not 2-manifold')
        while True:
            #First fix non-manifold edges
            print('Fixing non-manifold edges')
            meshset.select_non_manifold_edges_()
            if meshset.current_mesh().selected_vertex_number() != 0:
                meshset.repair_non_manifold_edges_by_removing_faces()
            meshset.select_non_manifold_edges_()
            if meshset.current_mesh().selected_vertex_number() != 0:
                print('Failed to fix all non-manifold edges through edge removal, deleting remaining')
                meshset.delete_selected_vertices()

            print('Fixing non-manifold vertices')
            #Next, fix remaining non-manifold vertices
            meshset.select_non_manifold_vertices()
            if  meshset.current_mesh().selected_vertex_number() != 0:
                meshset.repair_non_manifold_vertices_by_splitting(vertdispratio = .05)
            meshset.select_non_manifold_vertices()

            #Maybe I need to iterate eiterh this method or the whole fix_non_manifold?
            if meshset.current_mesh().selected_vertex_number() != 0:
                print('Failed to fix all non-manifold vertices through vertex splitting, deleting remaining')
                meshset.delete_selected_vertices()

            meshset.close_holes(maxholesize = 150, selfintersection = False, newfaceselected = False)
            meshset.remove_unreferenced_vertices()
            meshset.current_mesh().compact()

            if is_2_manifold(meshset):
               break
    return meshset

def print_checks(meshset):
    print("__________________________________________")
    print(f'Is 2-manifold?:{is_2_manifold(meshset)}')
    print(f'# zero area faces:{zero_area_face_number(meshset)}')
    print(f'Self intersecting faces:{self_intersecting_face_number(meshset)}')
    print(f'Problematic faces:{problematic_face_number(meshset)}')
    print(f'Border vertices:{border_vertex_number(meshset)}')
    print("__________________________________________")

def fix_self_intersecting(meshset):
    #This needs work! Don't trust it!
    start_verts = meshset.current_mesh().vertex_number()
    meshset.select_self_intersecting_faces()
    start_intersecting = meshset.current_mesh().selected_face_number()
    print(f'Fixing {start_intersecting} self intersecting faces.')
    
    if start_intersecting > 0:
        #First try and edge flip
        meshset.dilate_selection()
        meshset.planar_flipping_optimization()
        meshset.select_none()

        if meshset.current_mesh().selected_face_number() > 0:
            #If that didn't work, delete and close holes
            meshset.select_vertices_from_faces(inclusive = False)
            print(f'{meshset.current_mesh().selected_vertex_number()} vertices deleted to fix self-intersecting faces.')
            meshset.delete_selected_faces()
            meshset.delete_selected_vertices()
            meshset.remove_zero_area_faces()
            meshset.remove_unreferenced_vertices()
            meshset = delete_small_disconnected_component(meshset)

            meshset.select_border()
            meshset.close_holes(maxholesize = 150, selfintersection = False, newfaceselected = False)
    
    return meshset, start_verts - meshset.current_mesh().vertex_number()

    #meshset.simplification_quadric_edge_collapse_decimation(targetperc = 0.2, preserveboundary = True, preservetopology = True)

    








