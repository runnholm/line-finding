# from collections import OrderedDict
import os
import numpy as np
from astropy.io import fits


def extract_image_extensions_key(filename):

    # frame number ids
    # frame_ids = np.arange(1, 16)


    """
    VM & AR -- setup dicts for DS9 display purposes
    """
    filters = ["F115W", "F150W", "F200W"]
    orients = ["C", "R"]
    extnames = ["SCI", "CONTAM"]

    hdu = fits.open(filename)

    ### Get the list of PAs for each filter
    pa_dict = {}
    for filt in filters:
        if f"N{filt:s}" in hdu[0].header:
            pa_dict[filt] = [hdu[0].header[f"{filt:s}{i+1:02d}"]
                                for i in range(hdu[0].header[f"N{filt:s}"])]

    ### Map the PAs to R/C orients
    orient_dict = {}
    for filt in filters:
        orient_dict[filt] = {}
        if filt in pa_dict:
            for pa in pa_dict[filt]:
                orient_dict[filt][hdu["SCI", f"{filt:s},{pa:.1f}"].header["GRIS0001"][-1]] = pa

    ### Setup the keys for the DS9 (15 frames)
    filter_orientations = []
    for filt in filters:
        for orient in orients:
            for extname in extnames:
                if orient in orient_dict[filt]:
                    filter_orientations.append((f"{extname:s}", f"{filt:s},{orient_dict[filt][orient]:.1f}"))
                else:
                    filter_orientations.append((f"{extname:s}", f"{filt:s},{orient:s}"))
        filter_orientations.append(("COMB", f"{filt:s}"))


    ### Populate with the actual HDUs
    spec2D_key = {}
    for val, key in enumerate(filter_orientations):
        if (",R" in key[1]) or (",C" in key[1]):
            ext = None
        elif "COMB" in key:
            filt = key[1]
            try:
                ext = hdu.index_of(("SCI", filt))
            except KeyError:
                ext = None
        else:
            # ext = hdu[*key[2:-2].split('\", \"')]
            ext = hdu.index_of(key)

        spec2D_key[key] = {"frame_id": val+1, "ext": ext}

    """
    # filter_orientations = [
    #     ("F115W,199.0", "SCI"),
    #     ("F115W,199.0", "CONTAM"),
    #     ("F115W,290.0", "SCI"),
    #     ("F115W,290.0", "CONTAM"),
    #     ("F115W", "COMB"),
    #     ("F150W,199.0", "SCI"),
    #     ("F150W,199.0", "CONTAM"),
    #     ("F150W,290.0", "SCI"),
    #     ("F150W,290.0", "CONTAM"),
    #     ("F150W", "COMB"),
    #     ("F200W,199.0", "SCI"),
    #     ("F200W,199.0", "CONTAM"),
    #     ("F200W,290.0", "SCI"),
    #     ("F200W,290.0", "CONTAM"),
    #     ("F200W", "COMB"),
    # ]

    # filter + orientation of SCI, CONTAM, and COMB images and their associated
    # frame number use to plot in DS9.
    spec2D_key = {
        key: {"frame_id": val, "ext": None}
        for key, val in zip(filter_orientations, frame_ids)
    }
    print(spec2D_key)

    with fits.open(filename) as hdu:
        n_ext = len(hdu)

        # loop over extensions to search for to identify extension belong to
        # which frame id in spec2D_key
        for ext in range(1, n_ext):

            # extract header information
            header = hdu[ext].header

            # check if name is in desied reference anmes
            if header["EXTNAME"] in ["SCI", "CONTAM"]:
                extname = header["EXTNAME"]
                extver = header["EXTVER"].split(",")

                # if extver is on the filter name w/out orientation
                # its the combined sci images images so label COMB
                if len(extver) == 1:
                    extname = "COMB"

                # update the master key to be associated with the correct
                # extension
                spec2D_key[(header["EXTVER"], extname)]["ext"] = ext
    """

    return spec2D_key


def display_spec2D_ds9():
    pass


def display_image_in_DS9(frame_number, image_file, region_file, verbose=True):
    """Display an image in ds9 via the xpa system. Should display an image and
    region file if given.:

    Parameters
    ----------
    frame_number: int
        frame number to display the image
    image_file: str
        image filename or path to display.
    region_file: str
        region file or pathj to display
    """
    # image_file path
    # frame number to add image to
    # add ,region file if ggiven
    ds9_title = "PASSAGE_DIRECT"

    if image_file is None:
        os.system(f"xpaset -p {ds9_title} frame {frame_number}")
        return

    if verbose:
        msg = f"Opening F{frame_number}: {os.path.basename(image_file)} | Region File: {region_file}"
        print(msg)

    os.system(f"xpaset -p {ds9_title} frame {frame_number}")  # Specify the frame
    os.system(f"xpaset -p {ds9_title} file {image_file}")

    if region_file:
        os.system(f"xpaset -p {ds9_title} regions load {region_file}")
    # os.system(f"xpaset -p {ds9_title} cmap bb")
    return


def display_images_in_DS9(images, region_files, root=None, verbose=True):
    """Main interface to display multi-images (direct and grism data)
    in DS9. This will produce a tiled display of the images where columns are
    direct image, grism image 1, grism image 2, and so on. Each row should be a
    different filter.

    TODO: Some of the logic I think can be improved by for not it works.

    Parameters
    ----------
    images: dict
        dictionary contains the image files in different filters to display.
    region_files: dict
        same as the images argument but for regions files to display. Default None
    root: str
        the root or base path the set of files. This to be removed
    verbose:
        messages to output to use if needed. Defaulf is True.

    Returns
    -------
    None
    """

    frame_num = 0
    image_dict = {}
    for i, (filter_name, filter_images) in enumerate(images.items(), start=1):
        for j, image_file in enumerate(filter_images, start=1):
            # print(f"(i, j) | ({i}, {j})")
            # row = (j - 1) // 3 + 1  # Calculate row number
            # col = (j - 1) % 3 + 1  # Calculate column number
            # frame_num = (i - 1) * 3 + (row - 1) * 3 + col
            frame_num += 1
            image_dict[frame_num] = {}

            # Build full paths to image and region files
            # this step should be removed doing to much
            # complete paths should be given already.
            if root:
                image_path = os.path.join(root, image_file)
            else:
                image_path = image_file

            region_file = region_files[filter_name][j - 1] if region_files else None
            # print(f"---DEBUG: WHAT IS THE REGION FILE? - {region_file}")
            # print(f"---DEBUG: WHAT IS THE IMAGE FILE? - {image_file}")

            # add logic to handle missing frames to  keep things symmetric
            # when displaying
            # if image_path is None:
            #     os.system(f"xpaset -p ds9 frame {frame_num}")
            #     continue

            # Check if the image file exists
            if not os.path.isfile(image_path):
                if verbose:
                    print(f"Error: Image file {image_path} does not exist.")
                image_dict[frame_num]["img"] = None
                image_dict[frame_num]["reg"] = None
                continue

            # Check if the region file exists
            # print(f"---DEBUG: checking region file - {region_file}")
            if region_file is None:
                is_region_file = False
            else:
                is_region_file = os.path.isfile(region_file)

            # print(f"---DEBUG: IS REGION FILE - {is_region_file}")

            if region_file and not is_region_file:
                if verbose:
                    print(f"Error: Region file {region_file} does not exist.")
                region_file = None

            # Display the image
            image_dict[frame_num]["img"] = image_path
            image_dict[frame_num]["reg"] = region_file

    for frame_num in image_dict:
        display_image_in_DS9(frame_num,
                             image_dict[frame_num]["img"],
                             image_dict[frame_num]["reg"], verbose=verbose)

    ds9_title = "PASSAGE_DIRECT"
    # Go to frame 1
    os.system(f"xpaset -p {ds9_title} frame 1")

    # Configure additional settings
    os.system(f"xpaset -p {ds9_title} tile")
    # os.system(f"xpaset -p {ds9_title} match frame wcs")
    os.system(f"xpaset -p {ds9_title} lock scale")
    # os.system(f"xpaset -p {ds9_title} zoom to fit")
    os.system(f"xpaset -p {ds9_title} scale mode zscale")
    os.system(f"xpaset -p {ds9_title} lock colorbar")
    #os.system(f"xpaset -p {ds9_title} lock scalelimits")

    # Figured out the angle is ~250 for PAR 28. Need to check if this is true for all.
    for framename in range(1,10):
        os.system(f"xpaset -p {ds9_title} frame " + str(framename))
        os.system(f"xpaset -p {ds9_title} wcs sky ecliptic")

    os.system(f"xpaset -p {ds9_title} frame 3")
    os.system(f"xpaset -p {ds9_title} match frame wcs")

    # if I match at open -- does it stay matched going forward?
    # Go to frame 1
    # os.system(f"xpaset -p {ds9_title} frame 3")
    # os.system(f"xpaset -p {ds9_title} match frame wcs")

    return
