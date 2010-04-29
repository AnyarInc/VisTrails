#!/usr/bin/env python

#FIXME !!! DOES NOT MERGE EXECUTION LOGS STORED IN VT FILE !!!

import sys
if '/vistrails/src/trunk/vistrails' not in sys.path:
    sys.path.append('/vistrails/src/trunk/vistrails')

from db.domain import DBAction, DBModule, DBConnection, DBPort, DBFunction, \
    DBParameter, DBLocation, DBPortSpec, DBTag, DBAnnotation, DBVistrail
from db.services import io

def merge_vistrails(vt, next_vt):
    id_remap = {}
    for action in next_vt.db_actions:
        new_action = action.do_copy(True, vt.idScope, id_remap)
        vt.db_add_action(new_action)

    for tag in next_vt.db_tags:
        if vt.db_has_tag_with_name(tag.db_name):
            copy_no = 2
            while vt.db_has_tag_with_name(tag.db_name + str(copy_no)):
                copy_no += 1
            tag.db_name = tag.db_name + str(copy_no)
        new_tag = tag.do_copy()
        if (DBAction.vtType, new_tag.db_id) in id_remap:
            new_tag.db_id = id_remap[(DBAction.vtType, new_tag.db_id)]
        vt.db_add_tag(new_tag)

    for annotation in next_vt.db_annotations:
        if vt.db_has_annotation_with_key(annotation.db_key):
            copy_no = 2
            while vt.db_has_annotation_with_key(annotation.db_key + \
                                                    str(copy_no)):
                copy_no += 1
            annotation.db_key = annotation.db_key + str(copy_no)
        new_annotation = annotation.do_copy(True, vt.idScope, id_remap)
        vt.db_add_annotation(new_annotation)

def main(out_fname, in_fnames):
    """main(out_fname: str, in_fnames: list<str>) -> None
    Combines all vistrails specified in in_fnames into a single vistrail
    by renumbering their ids

    """
    # FIXME this breaks when you use abstractions!
    (save_bundle, vt_save_dir) = io.open_bundle_from_zip_xml(DBVistrail.vtType, in_fnames[0])
    for in_fname in in_fnames[1:]:
        (new_save_bundle, new__save_dir) = io.open_bundle_from_zip_xml(DBVistrail.vtType, in_fname)
        merge_vistrails(save_bundle.vistrail, new_save_bundle.vistrail)
    io.save_bundle_to_zip_xml(save_bundle, out_fname)
    
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: %s [output filename] [list of input vistrails]" % \
            sys.argv[0]
        sys.exit(0)
    main(sys.argv[1], sys.argv[2:])
