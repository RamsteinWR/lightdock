#!/usr/bin/env python

"""Before launching the LightDock simulation, a setup step is required.

This step parses the input PDB structures, calculates the minimum ellipsoid 
containing each of them, calculates the swarms on the surface of the 
receptor and populates each swarm with random coordinates for each glowworm's
optimization vector.
"""

import argparse
import numpy as np
from lightdock.util.parser import SetupCommandLineParser
from lightdock.prep.simulation import read_input_structure, save_lightdock_structure, \
                                      calculate_starting_positions, prepare_results_environment, \
                                      create_setup_file, calculate_anm, parse_restraints_file, \
                                      get_restraints
from lightdock.constants import DEFAULT_LIGHTDOCK_PREFIX, DEFAULT_ELLIPSOID_DATA_EXTENSION, \
                                DEFAULT_NMODES_REC, DEFAULT_REC_NM_FILE, DEFAULT_NMODES_LIG, DEFAULT_LIG_NM_FILE
from lightdock.mathutil.ellipsoid import MinimumVolumeEllipsoid
from lightdock.util.logger import LoggingManager
from lightdock.error.lightdock_errors import LightDockError


log = LoggingManager.get_logger('lightdock_setup')


if __name__ == "__main__":

    try:
        parser = SetupCommandLineParser()
        args = parser.args

        # Read input structures
        receptor = read_input_structure(args.receptor_pdb, args.noxt)
        ligand = read_input_structure(args.ligand_pdb, args.noxt)
        
        # Move structures to origin
        rec_translation = receptor.move_to_origin()
        lig_translation = ligand.move_to_origin()

        # Calculate reference points for receptor
        log.info("Calculating reference points for receptor %s..." % args.receptor_pdb)
        rec_ellipsoid = MinimumVolumeEllipsoid(receptor.representative().coordinates)
        ellipsoid_data_file = "%s%s" % (DEFAULT_LIGHTDOCK_PREFIX % receptor.structure_file_names[0],
                                        DEFAULT_ELLIPSOID_DATA_EXTENSION)
        np.save(ellipsoid_data_file, np.array([rec_ellipsoid.center.copy()]))
        log.info("Done.")

        # Calculate reference points for ligand
        log.info("Calculating reference points for ligand %s..." % args.ligand_pdb)
        lig_ellipsoid = MinimumVolumeEllipsoid(ligand.representative().coordinates)
        ellipsoid_data_file = "%s%s" % (DEFAULT_LIGHTDOCK_PREFIX % ligand.structure_file_names[0],
                                        DEFAULT_ELLIPSOID_DATA_EXTENSION)
        np.save(ellipsoid_data_file, np.array([lig_ellipsoid.center.copy()]))
        log.info("Done.")

        # Save to file parsed structures
        save_lightdock_structure(receptor)
        save_lightdock_structure(ligand)

        # Calculate and save ANM if required
        if args.use_anm:
            calculate_anm(receptor, args.anm_rec, DEFAULT_REC_NM_FILE)
            calculate_anm(ligand, args.anm_lig, DEFAULT_LIG_NM_FILE)

        # Parse restraints if any:
        receptor_restraints = ligand_restraints = None
        if args.restraints:
            log.info("Reading restraints from %s" % args.restraints)
            restraints = parse_restraints_file(args.restraints)
            # Check if restraints have been defined for the ligand, but not to the receptor
            if len(restraints['ligand']) and not len(restrains['receptor']):
                raise LightDockError("Restraints defined for ligand, but not receptor. Try switching structures.")

            if not len(restraints['receptor']) and not len(restraints['ligand']):
                raise LightDockError("Restraints file specified, but not a single restraint found")

            # Check if restraints correspond with real residues
            receptor_restraints = get_restraints(receptor, restraints['receptor'])
            args.receptor_restraints = restraints['receptor']
            ligand_restraints = get_restraints(ligand, restraints['ligand'])
            args.ligand_restraints = restraints['ligand']

        # Calculate surface points (swarm centers) over receptor structure
        starting_points_files = calculate_starting_positions(receptor, ligand, 
                                                             args.swarms, args.glowworms, 
                                                             args.starting_points_seed,
                                                             receptor_restraints, ligand_restraints, 
                                                             rec_translation, lig_translation,
                                                             args.ftdock_file, args.use_anm, args.anm_seed,
                                                             args.anm_rec, args.anm_lig)
        if len(starting_points_files) != args.swarms:
            args.swarms = len(starting_points_files)
            log.info('Number of swarms is %d after applying restraints' % args.swarms)

        # Create simulation folders
        prepare_results_environment(args.swarms)

        # Dump to a setup file the actual configuration
        create_setup_file(args)

        log.info("LightDock setup OK")

    except LightDockError, error:
        log.error("LightDock setup failed. Please see:")
        log.error(error)