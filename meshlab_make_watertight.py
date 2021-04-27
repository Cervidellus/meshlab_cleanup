# %%

import pymeshlab

def make_watertight(meshset, ambient_occlussion_remove = True, fixSelfIntersecting = True):
    '''
    Makes a mesh watertight by iteratively deleting non-manifold vertices, 
    fixing self-intersecting edges, and removing border edges that cannot be closed.

    ambient_occlusion_remove can be used to first remove some of the internal mesh

    fix_self_intersecting will first try to fix self intersecting edges by edge flipping. 
    If that doesn't work, it will delete them and fix the holes. 
    '''
    #For initial cleanup
    meshset.remove_duplicate_faces()
    meshset.remove_duplicate_vertices()
    meshset.remove_zero_area_faces()
    meshset.remove_unreferenced_vertices()
    meshset.current_mesh().compact()

    if ambient_occlussion_remove:
        vertex_removal_ambient_occlusion(meshset)

    delete_small_disconnected_component(meshset)

    iteration = 0

    #iteratively fix_non_manifold_by_deletion, fix_self_intersecting(if option used) and remove border edges that can't be fixed
    while(True):
        iteration +=1
        print(f'Beginning iteration {iteration} of clean_mesh.')
        removed1 = fix_non_manifold_by_deletion(meshset)

        meshset.select_border()
        meshset.close_holes(maxholesize = 150, selfintersection = False, newfaceselected = False)
        meshset.select_none()

        if fixSelfIntersecting:
            removed2 = fix_self_intersecting(meshset)
        else:
            removed2 = 0

        if removed1 == 0 and removed2 == 0:
            meshset.select_none()
            meshset.select_border()
            #Check if there are still border edges, if so delete them and start another iteration
            if meshset.current_mesh().selected_vertex_number() != 0:
                meshset.delete_selected_faces()
                meshset.delete_selected_vertices()
                meshset.remove_zero_area_faces()
                meshset.remove_unreferenced_vertices()
                meshset.current_mesh().compact()
            else:
                break

def delete_small_disconnected_component(meshset):
    meshset.current_mesh().compact()
    meshset.select_small_disconnected_component()
    meshset.select_vertices_from_faces()
    meshset.delete_selected_faces()
    meshset.delete_selected_vertices()

def vertex_removal_ambient_occlusion(meshset):
    meshset.ambient_occlusion(reqviews = 512, usegpu = True, coneangle = 300)
    meshset.select_by_vertex_quality(minq = 0, maxq = 0.005)
    meshset.delete_selected_faces()
    meshset.delete_selected_vertices()

def fix_non_manifold_edges_by_deletion(meshset):
    start_vertices = meshset.current_mesh().vertex_number()
    while(True):
        meshset.select_non_manifold_edges_()
        selected_count = meshset.current_mesh().selected_vertex_number()
        if selected_count == 0:
            break
        
        meshset.delete_selected_faces()
        meshset.delete_selected_vertices()
        meshset.remove_zero_area_faces()
        meshset.remove_unreferenced_vertices()
        meshset.close_holes(newfaceselected = False)
    
    vertices_removed = start_vertices - meshset.current_mesh().vertex_number()
    return vertices_removed

def fix_non_manifold_vertices_by_deletion(meshset):
    start_vertices = meshset.current_mesh().vertex_number()
    while(True):
        meshset.select_non_manifold_vertices()
        selected_count = meshset.current_mesh().selected_vertex_number()
        if selected_count == 0:
            break
        meshset.delete_selected_vertices()
        meshset.remove_zero_area_faces()
        meshset.remove_unreferenced_vertices()
    delete_small_disconnected_component(meshset)
    vertices_removed = start_vertices - meshset.current_mesh().vertex_number()
    # print(f"{vertices_removed} vertices removed")
    return vertices_removed

def fix_non_manifold_by_deletion(meshset, delete_disconnected = True):
    start_vertices = meshset.current_mesh().vertex_number()
    
    try:
        while(True):
            removed_edge_deletion = fix_non_manifold_edges_by_deletion(meshset)
            removed_vertex_deletion = fix_non_manifold_vertices_by_deletion(meshset)
            if removed_edge_deletion == 0 and removed_vertex_deletion == 0:
                break
    except:
        print("exception")
    if delete_disconnected:
        delete_small_disconnected_component(meshset)
    
    removed = meshset.current_mesh().vertex_number() - start_vertices
    print(f"{removed} vertices removed by fix_non_manifold_by_deletion.")
    return removed

def fix_self_intersecting(meshset):
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
            delete_small_disconnected_component(meshset)

            meshset.select_border()
            meshset.close_holes(maxholesize = 150, selfintersection = False, newfaceselected = False)
    
    return start_verts - meshset.current_mesh().vertex_number()

    #meshset.simplification_quadric_edge_collapse_decimation(targetperc = 0.2, preserveboundary = True, preservetopology = True)

    








