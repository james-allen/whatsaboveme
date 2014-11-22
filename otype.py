import requests
from astropy.cosmology import WMAP9
import astropy.units as u

import re
from collections import namedtuple
import math

Otype = namedtuple(
    'Otype', ('name', 'condensed', 'explanation',
              'tweet_name', 'followup'))

OTYPES_LIST = [Otype(*o) for o in [
    ('Unknown', '?', 'Object of unknown nature', 'an object of unknown nature', None),
    ('Transient', 'ev', 'transient event', 'a transient object', None),
    ('Radio', 'Rad', 'Radio-source', 'a radio source', None),
    ('Radio(m)', 'mR', 'metric Radio-source', 'a metre-wave radio source', None),
    ('Radio(cm)', 'cm', 'centimetric Radio-source', 'a cm-wave radio source', None),
    ('Radio(mm)', 'mm', 'millimetric Radio-source', 'a mm-wave radio source', None),
    ('Radio(sub-mm)', 'smm', 'sub-millimetric source', 'a sub-mm radio source', None),
    ('HI', 'HI', 'HI (21cm) source', 'a source of emission from hydrogen', None),
    ('radioBurst', 'rB', 'radio Burst', 'a radio burst', None),
    ('Maser', 'Mas', 'Maser', 'a maser', None),
    ('IR', 'IR', 'Infra-Red source', 'an infrared source', None),
    ('IR>30um', 'FIR', 'Far-IR source (l >= 30 um)', 'a far-infrared source', None),
    ('IR<10um', 'NIR', 'Near-IR source (l < 10 um)', 'a near-infrared source', None),
    ('Red', 'red', 'Very red source', 'a very red object', None),
    ('RedExtreme', 'ERO', 'Extremely Red Object', 'an extremely red object', None),
    ('Blue', 'blu', 'Blue object', 'a blue object', None),
    ('UV', 'UV', 'UV-emission source', 'an ultraviolet source', None),
    ('X', 'X', 'X-ray source', 'an X-ray source', None),
    ('ULX?', 'UX?', 'Ultra-luminous X-ray candidate', 'a possible ultra-luminous X-ray source', None),
    ('ULX', 'ULX', 'Ultra-luminous X-ray source', 'an ultra-luminous X-ray source', None),
    ('gamma', 'gam', 'gamma-ray source', 'a gamma-ray source', None),
    ('gammaBurst', 'gB', 'gamma-ray Burst', 'a gamma-ray burst', None),
    ('Inexistent', 'err', 'Not an object (error, artefact, ...)', 'an error in the database', None),
    ('Gravitation', 'grv', 'Gravitational Source', 'a clump of dark matter', None),
    ('LensingEv', 'Lev', '(Micro)Lensing Event', 'a past microlensing event', None),
    ('Candidate_LensSystem', 'LS?', 'Possible gravitational lens System', 'a possible gravitational lens system', None),
    ('Candidate_Lens', 'Le?', 'Possible gravitational lens', 'a possible gravitational lens', None),
    ('Possible_lensImage', 'LI?', 'Possible gravitationally lensed image', 'a possible gravitationally lensed image', None),
    ('GravLens', 'gLe', 'Gravitational Lens', 'a gravitational lens', None),
    ('GravLensSystem', 'gLS', 'Gravitational Lens System (lens+images)', 'a gravitational lens system', None),
    ('Candidates', '..?', 'Candidate objects', 'a candidate object', None),
    ('Possible_G', 'G?', 'Possible Galaxy', 'a possible galaxy', None),
    ('Possible_SClG', 'SC?', 'Possible Supercluster of Galaxies', 'a possible supercluster of galaxies', None),
    ('Possible_ClG', 'C?G', 'Possible Cluster of Galaxies', 'a possible cluster of galaxies', None),
    ('Possible_GrG', 'Gr?', 'Possible Group of Galaxies', 'a possible group of galaxies', None),
    ('Candidate_**', '**?', 'Physical Binary Candidate', 'a candidate binary star system', None),
    ('Candidate_EB*', 'EB?', 'Eclipsing Binary Candidate', 'a candidate eclipsing binary star system', None),
    ('Candidate_Symb*', 'Sy?', 'Symbiotic Star Candidate', 'a candidate symbiotic star', None),
    ('Candidate_CV*', 'CV?', 'Cataclysmic Binary Candidate', 'a candidate cataclysmic binary star system', None),
    ('Candidate_Nova', 'No?', 'Nova Candidate', 'a candidate nova', None),
    ('Candidate_XB*', 'XB?', 'X-ray binary Candidate', 'a candidate X-ray binary system', None),
    ('Candidate_LMXB', 'LX?', 'Low-Mass X-ray binary Candidate', 'a candidate low-mass X-ray binary system', None),
    ('Candidate_HMXB', 'HX?', 'High-Mass X-ray binary Candidate', 'a candidate high-mass X-ray binary system', None),
    ('Candidate_Pec*', 'Pec?', 'Possible Peculiar Star', 'a possible peculiar star', None),
    ('Candidate_YSO', 'Y*?', 'Young Stellar Object Candidate', 'a candidate young stellar object', None),
    ('Candidate_pMS*', 'pr?', 'Pre-main sequence Star Candidate', 'a candidate pre-main sequence star', None),
    ('Candidate_TTau*', 'TT?', 'T Tau star Candidate', 'a candidate T Tauri star', None),
    ('Candidate_C*', 'C*?', 'Possible Carbon Star', 'a possible carbon star', None),
    ('Candidate_S*', 'S*?', 'Possible S Star', 'a possible S star', None),
    ('Candidate_OH', 'OH?', 'Possible Star with envelope of OH/IR type', 'a possible OH/IR star', None),
    ('Candidate_CH', 'CH?', 'Possible Star with envelope of CH type', 'a possible CH star', None),
    ('Candidate_WR*', 'WR?', 'Possible Wolf-Rayet Star', 'a possible Wolf-Rayet star', None),
    ('Candidate_Be*', 'Be?', 'Possible Be Star', 'a possible Be star', None),
    ('Candidate_Ae*', 'Ae?', 'Possible Herbig Ae/Be Star', 'a possible Herbig Ae/Be star', None),
    ('Candidate_HB*', 'HB?', 'Possible Horizontal Branch Star', 'a possible horizontal branch star', None),
    ('Candidate_RRLyr', 'RR?', 'Possible Star of RR Lyr type', 'a possible RR Lyrae variable star', None),
    ('Candidate_Cepheid', 'Ce?', 'Possible Cepheid', 'a possible Cepheid variable star', None),
    ('Candidate_RGB*', 'RB?', 'Possible Red Giant Branch star', 'a possible red giant branch star', None),
    ('Candidate_SG*', 'sg?', 'Possible Supergiant star', 'a possible supergiant star', None),
    ('Candidate_RSG*', 's?r', 'Possible Red supergiant star', 'a possible red supergiant star', None),
    ('Candidate_YSG*', 's?y', 'Possible Yellow supergiant star', 'a possible yellow supergiant star', None),
    ('Candidate_BSG*', 's?b', 'Possible Blue supergiant star', 'a possible blue supergiant star', None),
    ('Candidate_AGB*', 'AB?', 'Possible Asymptotic Giant Branch Star', 'a possible asymptotic giant branch star', None),
    ('Candidate_post-AGB*', 'pA?', 'Post-AGB Star Candidate', 'a candidate post-AGB star', None),
    ('Candidate_BSS', 'BS?', 'Candidate blue Straggler Star', 'a candidate blue straggler star', None),
    ('Candidate_WD*', 'WD?', 'White Dwarf Candidate', 'a candidate white dwarf', None),
    ('Candidate_NS', 'N*?', 'Neutron Star Candidate', 'a candidate neutron star', None),
    ('Candidate_BH', 'BH?', 'Black Hole Candidate', 'a candidate black hole', None),
    ('Candidate_SN*', 'SN?', 'SuperNova Candidate', 'a candidate supernova', None),
    ('Candidate_low-mass*', 'LM?', 'Low-mass star candidate', 'a candidate low-mass star', None),
    ('Candidate_brownD*', 'BD?', 'Brown Dwarf Candidate', 'a candidate brown dwarf', None),
    ('multiple_object', 'mul', 'Composite object', 'a composite object', None),
    ('Region', 'reg', 'Region defined in the sky', 'a region in the sky', None),
    ('Void', 'vid', 'Underdense region of the Universe', 'an underdense region', None),
    ('SuperClG', 'SCG', 'Supercluster of Galaxies', 'a supercluster of galaxies', None),
    ('ClG', 'ClG', 'Cluster of Galaxies', 'a cluster of galaxies', None),
    ('GroupG', 'GrG', 'Group of Galaxies', 'a group of galaxies', None),
    ('Compact_Gr_G', 'CGG', 'Compact Group of Galaxies', 'a compact group of galaxies', None),
    ('PairG', 'PaG', 'Pair of Galaxies', 'a pair of galaxies', None),
    ('IG', 'IG', 'Interacting Galaxies', 'a pair of interacting galaxies', None),
    ('Cl*?', 'C?*', 'Possible (open) star cluster', 'a possible star cluster', None),
    ('GlCl?', 'Gl?', 'Possible Globular Cluster', 'a possible globular cluster', None),
    ('Cl*', 'Cl*', 'Cluster of Stars', 'a cluster of stars', None),
    ('GlCl', 'GlC', 'Globular Cluster', 'a globular cluster', None),
    ('OpCl', 'OpC', 'Open (galactic) Cluster', 'an open cluster of stars', None),
    ('Assoc*', 'As*', 'Association of Stars', 'an association of stars', None),
    ('Stream*', 'St*', 'Stellar Stream', 'a stellar stream', None),
    ('MouvGroup', 'MGr', 'Moving Group', 'a moving group of stars', None),
    ('**', '**', 'Double or multiple star', 'a double or multiple star', None),
    ('EB*', 'EB*', 'Eclipsing binary', 'an eclipsing binary', None),
    ('EB*Algol', 'Al*', 'Eclipsing binary of Algol type (detached)', 'a detached eclipsing binary', None),
    ('EB*betLyr', 'bL*', 'Eclipsing binary of beta Lyr type (semi-detached)', 'a semi-detached eclipsing binary', None),
    ('EB*WUMa', 'WU*', 'Eclipsing binary of W UMa type (contact binary)', 'a contact binary star system', None),
    ('EB*Planet', 'EP*', 'Star showing eclipses by its planet', 'a star being eclipsed by its planet', None),
    ('SB*', 'SB*', 'Spectroscopic binary', 'a binary star system', None),
    ('EllipVar', 'El*', 'Ellipsoidal variable Star', 'an ellipsoidal variable star', None),
    ('Symbiotic*', 'Sy*', 'Symbiotic Star', 'a symbiotic star', None),
    ('CataclyV*', 'CV*', 'Cataclysmic Variable Star', 'a cataclysmic variable star', None),
    ('DQHer', 'DQ*', 'CV DQ Her type (intermediate polar)', 'an intermediate polar cataclysmic variable star', None),
    ('AMHer', 'AM*', 'CV of AM Her type (polar)', 'a polar cataclysmic variable star', None),
    ('Nova-like', 'NL*', 'Nova-like Star', 'a nova-like star', None),
    ('Nova', 'No*', 'Nova', 'a nova', None),
    ('DwarfNova', 'DN*', 'Dwarf Nova', 'a dwarf nova', None),
    ('XB', 'XB*', 'X-ray Binary', 'an X-ray binary system', None),
    ('LMXB', 'LXB', 'Low Mass X-ray Binary', 'a low-mass X-ray binary system', None),
    ('HMXB', 'HXB', 'High Mass X-ray Binary', 'a high-mass X-ray binary system', None),
    ('ISM', 'ISM', 'Interstellar matter', 'some interstellar matter', None),
    ('PartofCloud', 'PoC', 'Part of Cloud', 'part of a gas cloud', None),
    ('PN?', 'PN?', 'Possible Planetary Nebula', 'a possible planetary nebula', None),
    ('ComGlob', 'CGb', 'Cometary Globule', 'a cometary globule', None),
    ('Bubble', 'bub', 'Bubble', 'a bubble of ionised gas', None),
    ('EmObj', 'EmO', 'Emission Object', 'an emission object', None),
    ('Cloud', 'Cld', 'Cloud', 'a gas cloud', None),
    ('GalNeb', 'GNe', 'Galactic Nebula', 'a nebula in our Galaxy', None),
    ('BrNeb', 'BNe', 'Bright Nebula', 'a bright nebula', None),
    ('DkNeb', 'DNe', 'Dark Cloud (nebula)', 'a dark nebula', None),
    ('RfNeb', 'RNe', 'Reflection Nebula', 'a reflection nebula', None),
    ('MolCld', 'MoC', 'Molecular Cloud', 'a molecular cloud', None),
    ('Globule', 'glb', 'Globule (low-mass dark cloud)', 'a globule', None),
    ('denseCore', 'cor', 'Dense core', 'a dense core of gas', None),
    ('SFregion', 'SFR', 'Star forming region', 'a star-forming region', None),
    ('HVCld', 'HVC', 'High-velocity Cloud', 'a high-velocity cloud', None),
    ('HII', 'HII', 'HII (ionized) region', 'a region of ionised gas', None),
    ('PN', 'PN', 'Planetary Nebula', 'a planetary nebula', None),
    ('HIshell', 'sh', 'HI shell', 'a shell of hydrogen gas', None),
    ('SNR?', 'SR?', 'SuperNova Remnant Candidate', 'a candidate supernova remnant', None),
    ('SNR', 'SNR', 'SuperNova Remnant', 'a supernova remnant', None),
    ('Circumstellar', 'cir', 'CircumStellar matter', 'some circumstellar matter', None),
    ('outflow?', 'of?', 'Outflow candidate', 'a candidate outflow of material', None),
    ('Outflow', 'out', 'Outflow', 'an outflow of material', None),
    ('HH', 'HH', 'Herbig-Haro Object', 'a Herbig-Haro object', None),
    ('Star', '*', 'Star', 'a star', None),
    ('*inCl', '*iC', 'Star in Cluster', 'a star in a cluster', None),
    ('*inNeb', '*iN', 'Star in Nebula', 'a star in a nebula', None),
    ('*inAssoc', '*iA', 'Star in Association', 'a star in an association of stars', None),
    ('*in**', '*i*', 'Star in double system', 'a star in a double system', None),
    ('V*?', 'V*?', 'Star suspected of Variability', 'a possibly variable star', None),
    ('Pec*', 'Pe*', 'Peculiar Star', 'a peculiar star', None),
    ('HB*', 'HB*', 'Horizontal Branch Star', 'a horizontal branch star', None),
    ('YSO', 'Y*O', 'Young Stellar Object', 'a young stellar object', None),
    ('Ae*', 'Ae*', 'Herbig Ae/Be star', 'a Herbig Ae/Be star', None),
    ('Em*', 'Em*', 'Emission-line Star', 'an emission-line star', None),
    ('Be*', 'Be*', 'Be Star', 'a Be star', None),
    ('BlueStraggler', 'BS*', 'Blue Straggler Star', 'a blue straggler star', None),
    ('RGB*', 'RG*', 'Red Giant Branch star', 'a red giant branch star', None),
    ('AGB*', 'AB*', 'Asymptotic Giant Branch Star (He-burning)', 'an asymptotic giant branch star', None),
    ('C*', 'C*', 'Carbon Star', 'a carbon star', None),
    ('S*', 'S*', 'S Star', 'an S star', None),
    ('SG*', 'sg*', 'Evolved supergiant star', 'an evolved supergiant star', None),
    ('RedSG*', 's*r', 'Red supergiant star', 'a red supergiant star', None),
    ('YellowSG*', 's*y', 'Yellow supergiant star', 'a yellow supergiant star', None),
    ('BlueSG*', 's*b', 'Blue supergiant star', 'a blue supergiant star', None),
    ('post-AGB*', 'pA*', 'Post-AGB Star (proto-PN)', 'a post-AGB star', None),
    ('WD*', 'WD*', 'White Dwarf', 'a white dwarf', None),
    ('pulsWD*', 'ZZ*', 'Pulsating White Dwarf', 'a pulsating white dwarf', None),
    ('low-mass*', 'LM*', 'Low-mass star (M<1solMass)', 'a low-mass star', None),
    ('brownD*', 'BD*', 'Brown Dwarf (M<0.08solMass)', 'a brown dwarf', None),
    ('Neutron*', 'N*', 'Confirmed Neutron Star', 'a neutron star', None),
    ('OH/IR', 'OH*', 'OH/IR star', 'an OH/IR star', None),
    ('CH', 'CH*', 'Star with envelope of CH type', 'a CH star', None),
    ('pMS*', 'pr*', 'Pre-main sequence Star', 'a pre-main sequence star', None),
    ('TTau*', 'TT*', 'T Tau-type Star', 'a T Tauri-type star', None),
    ('WR*', 'WR*', 'Wolf-Rayet Star', 'a Wolf-Rayet star', None),
    ('PM*', 'PM*', 'High proper-motion Star', 'a star with high proper motion', None),
    ('HV*', 'HV*', 'High-velocity Star', 'a high-velocity star', None),
    ('V*', 'V*', 'Variable Star', 'a variable star', None),
    ('Irregular_V*', 'Ir*', 'Variable Star of irregular type', 'an irregular variable star', None),
    ('Orion_V*', 'Or*', 'Variable Star of Orion Type', 'an Orion variable star', None),
    ('Rapid_Irreg_V*', 'RI*', 'Variable Star with rapid variations', 'a rapidly variable star', None),
    ('Eruptive*', 'Er*', 'Eruptive variable Star', 'an eruptive variable star', None),
    ('Flare*', 'Fl*', 'Flare Star', 'a flare star', None),
    ('FUOr', 'FU*', 'Variable Star of FU Ori type', 'an FU Orionis variable star', None),
    ('Erupt*RCrB', 'RC*', 'Variable Star of R CrB type', 'an R Coronae Borealis variable star', None),
    ('RotV*', 'Ro*', 'Rotationally variable Star', 'a rotationally variable star', None),
    ('RotV*alf2CVn', 'a2*', 'Variable Star of alpha2 CVn type', 'an alpha2 Canum Venaticorum variable star', None),
    ('Pulsar', 'Psr', 'Pulsar', 'a pulsar', None),
    ('BYDra', 'BY*', 'Variable of BY Dra type', 'a BY Draconis variable star', None),
    ('RSCVn', 'RS*', 'Variable of RS CVn type', 'an RS Canum Venaticorum variable star', None),
    ('PulsV*', 'Pu*', 'Pulsating variable Star', 'a pulsating variable star', None),
    ('RRLyr', 'RR*', 'Variable Star of RR Lyr type', 'an RR Lyrae variable star', None),
    ('Cepheid', 'Ce*', 'Cepheid variable Star', 'a Cepheid variable star', None),
    ('PulsV*delSct', 'dS*', 'Variable Star of delta Sct type', 'a delta Scuti variable star', None),
    ('PulsV*RVTau', 'RV*', 'Variable Star of RV Tau type', 'an RV Tauri variable star', None),
    ('PulsV*WVir', 'WV*', 'Variable Star of W Vir type', 'a W Virginis variable star', None),
    ('PulsV*bCep', 'bC*', 'Variable Star of beta Cep type', 'a beta Cephei variable star', None),
    ('deltaCep', 'cC*', 'Classical Cepheid (delta Cep type)', 'a classical Cepheid variable star', None),
    ('gammaDor', 'gD*', 'Variable Star of gamma Dor type', 'a gamma Doradus variable star', None),
    ('pulsV*SX', 'SX*', 'Variable Star of SX Phe type (subdwarf)', 'an SX Phoenicis variable star', None),
    ('LPV*', 'LP*', 'Long-period variable star', 'a long-period variable star', None),
    ('Mira', 'Mi*', 'Variable Star of Mira Cet type', 'a Mira Ceti variable star', None),
    ('semi-regV*', 'sr*', 'Semi-regular pulsating Star', 'a semi-regular pulsating star', None),
    ('SN', 'SN*', 'SuperNova', 'a supernova', None),
    ('Sub-stellar', 'su*', 'Sub-stellar object', 'a sub-stellar object', None),
    ('Planet?', 'Pl?', 'Extra-solar Planet Candidate', 'a candidate extra-solar planet', None),
    ('Planet', 'Pl', 'Extra-solar Confirmed Planet', 'an extra-solar planet', None),
    ('Galaxy', 'G', 'Galaxy', 'a galaxy', None),
    ('PartofG', 'PoG', 'Part of a Galaxy', 'a part of a galaxy', None),
    ('GinCl', 'GiC', 'Galaxy in Cluster of Galaxies', 'a galaxy in a galaxy cluster', None),
    ('BClG', 'BiC', 'Brightest galaxy in a Cluster (BCG)', 'a brightest galaxy in a cluster', None),
    ('GinGroup', 'GiG', 'Galaxy in Group of Galaxies', 'a galaxy in a group of galaxies', None),
    ('GinPair', 'GiP', 'Galaxy in Pair of Galaxies', 'one of a pair of galaxies', None),
    ('High_z_G', 'HzG', 'Galaxy with high redshift', 'a high-redshift galaxy', None),
    ('AbsLineSystem', 'ALS', 'Absorption Line system', 'an absorption line system', None),
    ('Ly-alpha_ALS', 'LyA', 'Ly alpha Absorption Line system', 'a Lyman-alpha absorption line system', None),
    ('DLy-alpha_ALS', 'DLA', 'Damped Ly-alpha Absorption Line system', 'a damped Lyman-alpha absorption line system', None),
    ('metal_ALS', 'mAL', 'metallic Absorption Line system', 'a metallic absorption line system', None),
    ('Ly-limit_ALS', 'LLS', 'Lyman limit system', 'a Lyman limit system', None),
    ('Broad_ALS', 'BAL', 'Broad Absorption Line system', 'a broad absorption line system', None),
    ('RadioG', 'rG', 'Radio Galaxy', 'a galaxy emitting radio waves', None),
    ('HII_G', 'H2G', 'HII Galaxy', 'a galaxy with ionised hydrogen', None),
    ('LSB_G', 'LSB', 'Low Surface Brightness Galaxy', 'a galaxy with low surface brightness', None),
    ('AGN_Candidate', 'AG?', 'Possible Active Galaxy Nucleus', 'a possible active galactic nucleus', None),
    ('QSO_Candidate', 'Q?', 'Possible Quasar', 'a possible quasar', None),
    ('Blazar_Candidate', 'Bz?', 'Possible Blazar', 'a possible blazar', None),
    ('BLLac_Candidate', 'BL?', 'Possible BL Lac', 'a possible BL Lac object', None),
    ('EmG', 'EmG', 'Emission-line galaxy', 'an emission-line galaxy', None),
    ('StarburstG', 'SBG', 'Starburst Galaxy', 'a starburst galaxy', None),
    ('BlueCompG', 'bCG', 'Blue compact Galaxy', 'a blue compact galaxy', None),
    ('LensedImage', 'LeI', 'Gravitationally Lensed Image', 'a gravitationally lensed image', None),
    ('LensedG', 'LeG', 'Gravitationally Lensed Image of a Galaxy', 'a gravitationally lensed image of a galaxy', None),
    ('LensedQ', 'LeQ', 'Gravitationally Lensed Image of a Quasar', 'a gravitationally lensed image of a quasar', None),
    ('AGN', 'AGN', 'Active Galaxy Nucleus', 'an active galactic nucleus', None),
    ('LINER', 'LIN', 'LINER-type Active Galaxy Nucleus', 'a LINER galaxy', None),
    ('Seyfert', 'SyG', 'Seyfert Galaxy', 'a Seyfert galaxy', None),
    ('Seyfert_1', 'Sy1', 'Seyfert 1 Galaxy', 'a Seyfert 1 galaxy', None),
    ('Seyfert_2', 'Sy2', 'Seyfert 2 Galaxy', 'a Seyfert 2 galaxy', None),
    ('Blazar', 'Bla', 'Blazar', 'a blazar', None),
    ('BLLac', 'BLL', 'BL Lac - type object', 'a BL Lac object', None),
    ('OVV', 'OVV', 'Optically Violently Variable object', 'an optically violently variable object', None),
    ('QSO', 'QSO', 'Quasar', 'a quasar', None)]]

OTYPES_DICT = {
    otype.name: otype for otype in OTYPES_LIST}

def info(obj):
    """Return HTML info about a specific object."""
    if obj['type'] == 'Star':
        text = '<p>There are around 300 billion stars in our galaxy, the Milky Way. In general, the most massive stars are the most luminous, but they also live for a shorter time. How bright a star appears from Earth also depends on how close to us it is.</p>'
    elif obj['type'] == 'IR':
        text = "<p>We don't know much about this object except that it emits plenty of infrared light. It might be a small, cool star or a distant galaxy."
        if not obj['mag']:
            text += " Because it's fainter in visible light than in the infrared, you might not be able to see anything in the image."
        text += '</p>'
    elif obj['type'] == 'Galaxy':
        text = "<p>Galaxies can contain hundreds of billions of stars, or sometimes even more. Because they are so far away, we normally can't see the individual stars. Instead we see the total light from all of them together."
        if obj['ze_redshift']:
            text += " This particular galaxy has been measured to be about {} light years away.".format(wordify_number(distance(obj['ze_redshift'])))
        text += '</p>'
    else:
        text = ''
    if obj['mag']:
        text += '<p>{} has a magnitude of {}, '.format(obj['name'], obj['mag'])
        if obj['mag'] < 3.0:
            text += 'which means it can be seen quite easily with the naked eye.'
        elif obj['mag'] < 6.0:
            text += 'which means it can be seen with the naked eye on a dark night.'
        elif obj['mag'] < 9.5:
            text += 'which means it can be seen with a good pair of binoculars.'
        elif obj['mag'] < 13.0:
            text += 'which means it can be seen with a good telescope.'
        else:
            text += 'which means it is too faint to be seen without a professional-quality telescope.'
        text += '</p>'
    return text

def distance(redshift):
    """Return comoving distance in light years for a given redshift."""
    return WMAP9.comoving_distance(redshift).to(u.lyr).value

def round_to_n(x, n):
    """Round x to n significant figures."""
    return int(round(x, -int(math.floor(math.log10(x))) + (n - 1)))

def wordify_number(number):
    """Present the number as a string with words like 'billion'."""
    if number < 10.0:
        factor = int(round(number))
        name = ''
    else:
        rounded = round_to_n(number, 2)
        named_numbers = (
            (1.0, ''), (1e6, ' million'), (1e9, ' billion'),
            (1e12, ' trillion'))
        for idx, (denominator, name) in enumerate(named_numbers):
            if denominator > rounded:
                idx_use = idx - 1
                break
        else:
            return wordify_number(number / denominator) + name
        denominator, name = named_numbers[idx_use]
        factor = int(round_to_n(number / denominator, 2))
    return '{}{}'.format(factor, name)

def count_otypes(verbose=True):
    """Return a dict of the number of each otype in Simbad."""
    return {otype[0]: count_single_otype(otype[1], verbose=verbose)
            for otype in OTYPES_LIST}

def count_single_otype(condensed_name, verbose=True):
    """Return the number of objects with that otype in Simbad."""
    req = requests.get(
        'http://simbad.u-strasbg.fr/simbad/sim-sam',
        params={'OutputMode':'COUNT',
                'Criteria':"otype = '{}'".format(condensed_name)})
    match = re.search(r'<TD>\n(?P<num>\d+)\n.+</TD>', req.text)
    if match:
        num = int(match.group('num'))
    else:
        num = 0
    if verbose:
        print condensed_name, num
    return num

# Results obtained on 8/11/2014
# Possible_SClG    0    0.0
# Candidates    0    0.0
# Candidate_Pec*    0    0.0
# Candidate_OH    0    0.0
# Inexistent    0    0.0
# Radio(m)    0    0.0
# Candidate_Ae*    0    0.0
# metal_ALS    0    0.0
# Candidate_CH    0    0.0
# OVV    0    0.0
# Sub-stellar    2    1.71145867794e-07
# Candidate_BSG*    3    2.56718801691e-07
# Gravitation    4    3.42291735589e-07
# radioBurst    6    5.13437603383e-07
# Candidate_LensSystem    10    8.55729338971e-07
# Candidate_Symb*    10    8.55729338971e-07
# Stream*    19    1.62588574405e-06
# Candidate_HMXB    19    1.62588574405e-06
# MouvGroup    20    1.71145867794e-06
# Candidate_LMXB    21    1.79703161184e-06
# Candidate_BSS    24    2.05375041353e-06
# Ae*    29    2.48161508302e-06
# EB*Planet    31    2.65276095081e-06
# Candidate_Cepheid    33    2.82390681861e-06
# DQHer    39    3.33734442199e-06
# FUOr    40    3.42291735589e-06
# CH    40    3.42291735589e-06
# High_z_G    40    3.42291735589e-06
# Broad_ALS    42    3.59406322368e-06
# Ly-alpha_ALS    48    4.10750082706e-06
# Candidate_Nova    54    4.62093843045e-06
# Neutron*    55    4.70651136434e-06
# Candidate_RRLyr    57    4.87765723214e-06
# Candidate_XB*    66    5.64781363721e-06
# Eruptive*    69    5.9045324389e-06
# Candidate_SG*    71    6.0756783067e-06
# Candidate_NS    79    6.76026177787e-06
# Possible_G    80    6.84583471177e-06
# Possible_lensImage    85    7.27369938126e-06
# AMHer    87    7.44484524905e-06
# ComGlob    100    8.55729338971e-06
# Candidate_YSG*    102    8.72843925751e-06
# Candidate_CV*    107    9.15630392699e-06
# Nova-like    109    9.32744979479e-06
# Candidate_WR*    111    9.49859566258e-06
# SFregion    112    9.58416859648e-06
# Candidate_Lens    112    9.58416859648e-06
# Circumstellar    122    1.04398979355e-05
# Possible_GrG    125    1.06966167371e-05
# ULX?    141    1.20657836795e-05
# BlueCompG    145    1.24080754151e-05
# Ly-limit_ALS    147    1.25792212829e-05
# GalNeb    150    1.28359400846e-05
# Erupt*RCrB    150    1.28359400846e-05
# Candidate_BH    151    1.29215130185e-05
# Outflow    159    1.36060964896e-05
# SG*    170    1.45473987625e-05
# Candidate_S*    179    1.53175551676e-05
# Candidate_low-mass*    183    1.56598469032e-05
# Void    210    1.79703161184e-05
# LensedQ    212    1.81414619862e-05
# pulsWD*    220    1.88260454574e-05
# Symbiotic*    230    1.96817747963e-05
# BrNeb    241    2.06230770692e-05
# BLLac_Candidate    242    2.07086500031e-05
# PulsV*RVTau    261    2.23345357472e-05
# Red    269    2.30191192183e-05
# Rapid_Irreg_V*    284    2.43027132268e-05
# HV*    284    2.43027132268e-05
# ULX    303    2.59285989708e-05
# Seyfert    303    2.59285989708e-05
# Globule    306    2.61853177725e-05
# PulsV*bCep    317    2.71266200454e-05
# Candidate_post-AGB*    347    2.96938080623e-05
# gammaDor    370    3.16619855419e-05
# GravLensSystem    376    3.21754231453e-05
# Cl*?    404    3.45714652944e-05
# LMXB    423    3.61973510385e-05
# multiple_object    424    3.62829239724e-05
# pulsV*SX    447    3.8251101452e-05
# post-AGB*    454    3.88501119893e-05
# EllipVar    481    4.11605812045e-05
# BlueSG*    509    4.35566233536e-05
# RSCVn    510    4.36421962875e-05
# outflow?    511    4.37277692214e-05
# RotV*alf2CVn    515    4.4070060957e-05
# YellowSG*    516    4.41556338909e-05
# Candidate_TTau*    555    4.74929783129e-05
# DwarfNova    639    5.46811047603e-05
# GravLens    702    6.00721995958e-05
# DLy-alpha_ALS    725    6.20403770754e-05
# PulsV*WVir    749    6.4094127489e-05
# Bubble    863    7.38494419532e-05
# SNR?    867    7.41917336888e-05
# LINER    887    7.59031923668e-05
# Region    917    7.84703803837e-05
# BYDra    969    8.29201729463e-05
# LensedG    1026    8.77978301785e-05
# Candidate_brownD*    1043    8.92525700547e-05
# StarburstG    1052    9.00227264598e-05
# CataclyV*    1056    9.03650181954e-05
# Blazar_Candidate    1098    9.39590814191e-05
# SuperClG    1118    9.5670540097e-05
# RedSG*    1154    9.87511657173e-05
# RedExtreme    1213    0.000103799968817
# Candidate_C*    1215    0.000103971114685
# Pec*    1217    0.000104142260553
# OH/IR    1253    0.000107222886173
# LensedImage    1318    0.000112785126876
# Candidate_SN*    1339    0.000114582158488
# WR*    1369    0.000117149346505
# HMXB    1373    0.000117491638241
# XB    1422    0.000121684712002
# Candidate_**    1441    0.000123310597746
# S*    1510    0.000129215130185
# SNR    1545    0.000132210182871
# Candidate_Be*    1584    0.000135547527293
# EB*betLyr    1590    0.000136060964896
# Irregular_V*    1613    0.000138029142376
# Transient    1654    0.000141537632666
# Be*    1708    0.000146158571096
# HIshell    1719    0.000147099873369
# Planet    1741    0.000148982477915
# RfNeb    1782    0.000152490968205
# Nova    1783    0.000152576541139
# BLLac    1865    0.000159593521718
# IR>30um    2140    0.00018312607854
# Possible_ClG    2178    0.000186377850028
# TTau*    2415    0.000206658635362
# Pulsar    2434    0.000208284521106
# Orion_V*    2498    0.000213761188875
# Flare*    2588    0.000221462752926
# Candidate_pMS*    2747    0.000235068849415
# Candidate_EB*    2909    0.000248931664707
# IG    3144    0.000269041304173
# Blazar    3258    0.000278796618637
# HH    3426    0.000293172871532
# *inNeb    3468    0.000296766934755
# V*?    3477    0.00029753709116
# Planet?    3505    0.000299933133309
# Candidate_RSG*    3576    0.000306008811616
# brownD*    3679    0.000314822823808
# OpCl    3705    0.000317047720089
# PartofG    3851    0.000329541368438
# denseCore    3961    0.000338954391167
# gamma    4017    0.000343746475465
# BlueStraggler    4024    0.000344345486002
# HII_G    4079    0.000349051997366
# PairG    4335    0.000370958668444
# deltaCep    4420    0.000378232367825
# PN?    4470    0.00038251101452
# AGB*    4517    0.000386532942413
# ISM    4671    0.000399711174234
# PulsV*delSct    4697    0.000401936070515
# Assoc*    4887    0.000418194927955
# Candidate_HB*    4888    0.000418280500889
# HVCld    4997    0.000427607950684
# EB*WUMa    5062    0.000433170191387
# Seyfert_2    5064    0.000433341337255
# AGN_Candidate    5095    0.000435994098206
# Maser    5591    0.000478438273419
# GinPair    6041    0.000516946093673
# pMS*    6105    0.000522422761442
# PartofCloud    6281    0.000537483597808
# AbsLineSystem    6287    0.000537997035411
# Radio(cm)    6316    0.000540478650494
# EB*Algol    6635    0.000567776416407
# Unknown    6872    0.000588057201741
# SB*    6983    0.000597555797404
# BClG    7081    0.000605941944926
# MolCld    7392    0.000632555127368
# PulsV*    7718    0.000660451903818
# RotV*    7773    0.000665158415182
# LSB_G    7908    0.000676710761259
# gammaBurst    8507    0.000727968948663
# Cloud    8795    0.000752613953625
# SN    9030    0.000772723593091
# Radio(sub-mm)    10489    0.000897574503647
# Mira    10777    0.000922219508609
# PN    11159    0.000954908369358
# HI    11457    0.000980409103659
# IR<10um    11872    0.00101592187123
# Radio(mm)    12503    0.00106991839252
# EmObj    12887    0.00110277839913
# Cepheid    13544    0.0011589998167
# GlCl?    14574    0.00124713993862
# RGB*    15418    0.00131936349483
# Seyfert_1    15611    0.00133587907107
# *inAssoc    15794    0.00135153891797
# GlCl    16727    0.0014313784653
# Candidate_WD*    17183    0.00147039972315
# HB*    18633    0.00159448047731
# Cl*    18974    0.00162366084776
# EB*    19060    0.00163102012008
# Blue    19335    0.0016545526769
# semi-regV*    20105    0.001720443836
# WD*    20474    0.00175202024861
# GroupG    20920    0.00179018577713
# Em*    21375    0.00182912146205
# RadioG    22102    0.00189133298499
# C*    23823    0.00203860400423
# Candidate_YSO    26483    0.0022662280084
# YSO    28231    0.00241580949685
# DkNeb    28640    0.00245080882681
# ClG    31303    0.00267868954978
# HII    34297    0.00293489491387
# EmG    39208    0.00335514359224
# QSO_Candidate    41864    0.00358242530467
# low-mass*    46306    0.00396254027704
# *in**    55555    0.00475400434266
# Candidate_AGB*    59129    0.0050598420084
# RRLyr    62315    0.0053324773758
# AGN    74253    0.00635404706066
# Compact_Gr_G    76826    0.00657422621958
# LPV*    76870    0.00657799142867
# UV    91260    0.00780938594745
# **    99450    0.00851022827607
# GinCl    120792    0.0103365258313
# LensingEv    132667    0.0113527044213
# Candidate_RGB*    134349    0.0114966380961
# PM*    155804    0.0133326053929
# QSO    157499    0.0134776515159
# X    234938    0.0201043339439
# V*    242606    0.020760507201
# GinGroup    343981    0.0294354633749
# *inCl    382546    0.0327355835706
# Radio    500599    0.042837725136
# Galaxy    1839642    0.15742356326
# IR    2207854    0.188932544397
# Star    3653977    0.312681532283
