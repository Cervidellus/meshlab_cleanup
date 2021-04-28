# %%

import pymeshlab

##Important! basic_cleanup is removing duplicate vertices, BUT I need the duplicate vertices to make it manifold. 


def make_watertight(meshset):
    '''
    Makes a mesh watertight.
    First fixes non-manifold edges, or deleted the vertices.
    Then fixes  non-manifold vertices, or deletes the vertices.
    Then closes hole.
    returns the number of vertices removed.
    '''
    initial_verts = meshset.current_mesh().vertex_number() 

    i = 0
    while(True):
        i +=1
        print(f'Starting iteration {i} of make watertight.')

        basic_cleanup(meshset)

        print("Fixing non-manifold edges.")
        removed1 = fix_non_manifold_edges(meshset)
        print(f'Removed {removed1} vertices in fix_non_manifold_edges\n\n')

        basic_cleanup(meshset)

        print("Fixing non-manifold vertices.")
        removed2 = fix_non_manifold_vertices(meshset) 
        print(f'Removed {removed2} vertices in fix_non_manifold_vertices')

        basic_cleanup(meshset)

        print("Closing holes")
        meshset.close_holes(maxholesize = 150, selfintersection = False, newfaceselected = False)
        meshset.select_border()
        border_verts = meshset.current_mesh().selected_vertex_number()
        print(f'{border_verts} border vertices left after close_holes')
        if border_verts != 0:
            print("Failed to close all holes")

        basic_cleanup(meshset)

        meshset.select_none()    
        meshset.select_non_manifold_edges_()
        bad_edge_verts = meshset.current_mesh().selected_vertex_number()
        meshset.select_none()
        meshset.select_non_manifold_vertices()
        bad_verts = meshset.current_mesh().selected_vertex_number()



        print(f'{bad_edge_verts} non-manifold edge vertices and {bad_verts} non-manifold vertices at the end of iteration {i} of make_watertight.')
        print('')

        if bad_edge_verts == 0 and bad_verts == 0:
         break

    print('')
    return initial_verts - meshset.current_mesh().vertex_number()

def basic_cleanup(meshset):
    #seems to take a long time? Figure it out?
    #print('basic:cleanup remove dup faces')
    meshset.remove_duplicate_faces()
    #print('basic:cleanup remove dup verts')
    meshset.remove_duplicate_vertices()
    #print('basic:cleanup remove zero area')
    meshset.remove_zero_area_faces()
    #print('basic:cleanup remove unreferenced')
    meshset.remove_unreferenced_vertices()
    #print('basic:cleanup compact')
    meshset.current_mesh().compact()

def delete_small_disconnected_component(meshset):
    meshset.select_small_disconnected_component()
    meshset.select_vertices_from_faces()
    meshset.delete_selected_faces()
    meshset.delete_selected_vertices()

def vertex_removal_ambient_occlusion(meshset):
    meshset.ambient_occlusion(reqviews = 512, usegpu = True, coneangle = 512)
    meshset.select_by_vertex_quality(minq = 0, maxq = 0.005)
    meshset.delete_selected_faces()
    meshset.delete_selected_vertices()

def fix_non_manifold_edges(meshset):
    start_verts = meshset.current_mesh().vertex_number() 
    meshset.select_non_manifold_edges_()
    bad_edge_verts =  meshset.current_mesh().selected_vertex_number()

    if bad_edge_verts != 0:
        #first try repair
        i = 0
        while(True):
            i += 1
            start_bad = bad_edge_verts
            print(f'starting iteration {i} of fix_non_manifold_edges by splitting with {start_bad} bad vertices.')
            meshset.repair_non_manifold_edges_by_splitting_vertices()#fails here....
            meshset.select_non_manifold_edges_()
            bad_edge_verts = meshset.current_mesh().selected_vertex_number()
            print(f'{start_bad} startbad. {bad_edge_verts} bad_edge_verts at end of iteration {i} of fix_non_manifold_edges_by_splitting.')
            print('')
            basic_cleanup(meshset)
            if bad_edge_verts == start_bad or bad_edge_verts == 0:
                break
    
        #if cannot be repaired, remove
        if bad_edge_verts != 0:
            print('Not all non-manifold edges fixed. Removing faces from non-manifold edges.') 
            i = 0
            while(True):
                i += 1
                start_bad = bad_edge_verts
                print(f'starting iteration {i} of fix_non_manifold_edges_by_removing_faces with {start_bad} bad vertices.')
                meshset.repair_non_manifold_edges_by_removing_faces()
                basic_cleanup(meshset)
                meshset.select_non_manifold_edges_()
                bad_edge_verts = meshset.current_mesh().selected_vertex_number()
                print(f'{start_bad} startbad. {bad_edge_verts} bad_edge_verts at end of iteration {i} of repair_non_manifold_edges_by_removing_face.')
                if bad_edge_verts == start_bad or bad_edge_verts == 0:
                    break 

    else:
        print('No non-manifold edges to fix')

    if bad_edge_verts != 0:
        print("Was not able to fix all non-manifold edges.")

    print(f'start_verts:{start_verts}, current_verts: {meshset.current_mesh().vertex_number()}')

    return start_verts - meshset.current_mesh().vertex_number()











def fix_non_manifold_vertices(meshset):
    start_verts = meshset.current_mesh().vertex_number()
    meshset.select_non_manifold_vertices()
    bad_verts =  meshset.current_mesh().selected_vertex_number()

    if bad_verts != 0:
        
        #Need to iterate this:
        i = 0
        while(True):
            i +=1
            print(f'starting iteration {i} of fix_non_manifold_vertices {bad_verts} bad vertices.')
            initial_bad = bad_verts#not used?
            #first try repair
            
            while(True):
                print(f'Current verts start repairbysplitting:{meshset.current_mesh().vertex_number()}')
                start_bad = bad_verts
                meshset.repair_non_manifold_vertices_by_splitting(vertdispratio = 100)#I don't know what this number means!
                meshset.select_none()
                meshset.select_non_manifold_vertices()
                bad_verts = meshset.current_mesh().selected_vertex_number()
                print(f'Current verts finish repairbysplitting:{meshset.current_mesh().vertex_number()}')
                if bad_verts == start_bad or bad_verts == 0:
                    break
            

            #If cannot, delete vertices
            while(True):
                print(f'Current verts start deleteverts:{meshset.current_mesh().vertex_number()}')
                start_bad = bad_verts
                meshset.select_none()
                meshset.select_non_manifold_vertices()
                bad_verts = meshset.current_mesh().selected_vertex_number()
                print(f'Deleting {bad_verts}')
                meshset.delete_selected_vertices()
                print(f'Current verts finish delteverts:{meshset.current_mesh().vertex_number()}')
                if bad_verts == start_bad or bad_verts == 0:
                    break   
        
            if bad_verts == 0:
                print(f'All non-manifold vertices fixed in iteration {i} of fix_non_manifold_vertices')
                print(f'Current verts before break:{meshset.current_mesh().vertex_number()}')
                break

        if bad_verts != 0:
            print("Was not able to fix all non-manifold vertices")
        print(f'Current verts before final cleanup:{meshset.current_mesh().vertex_number()}')
        basic_cleanup(meshset)#IMPORTANT, here it merges teh duplicate vertices!
        print(f'Current verts after final cleanup:{meshset.current_mesh().vertex_number()}')
    else:
        print('No bad vertices to fix in fix_non_manifold_vertices.')
    print('')
    print(f'I am about to return {start_verts} - {meshset.current_mesh().vertex_number()}')
    #retunrs 0, when it should have fixed some?
    return start_verts - meshset.current_mesh().vertex_number()












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
            delete_small_disconnected_component(meshset)

            meshset.select_border()
            meshset.close_holes(maxholesize = 150, selfintersection = False, newfaceselected = False)
    
    return start_verts - meshset.current_mesh().vertex_number()

    #meshset.simplification_quadric_edge_collapse_decimation(targetperc = 0.2, preserveboundary = True, preservetopology = True)

    








