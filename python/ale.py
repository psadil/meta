import os
from typing import Union, Optional

import pandas as pd

import nimare
from nimare.meta.cbma import ALE
from nimare.transforms import ImagesToCoordinates,transform_images

def as_dict(d: tuple) -> dict:
  ds = {
    d.exp: {
      'contrasts': {
        "1": {
          "images": {
            't': d.t,
            'varcope': d.varcope
            },
            "metadata": {
              "sample_sizes": [d.n_sub]
              } 
            }
          }
        }
      }

  return ds

def do_ale(
  d: pd.DataFrame,
  in_dir: Union[str, bytes, os.PathLike],
  out_dir: Union[str, bytes, os.PathLike] = os.getcwd(),
  prefix: Optional[str] = None,
  mask: Union[str, bytes, os.PathLike] = os.path.join(os.getenv("FSLDIR"), "data", "standard", "MNI152_T1_2mm_brain_mask.nii.gz"),
  z_threshold: float = 2.3,
  remove_subpeaks: bool = True,
  two_sided: bool = False,
  min_distance: float = 0
  ) -> Union[str, bytes, os.PathLike]:

    x = {}
    for row in d.itertuples():
      x.update(as_dict(row))
          
    dset = nimare.dataset.Dataset(x, mask=mask)
    dset.update_path(new_path=in_dir)

    temp_images = transform_images(
      dset.images,
      target="z",
      masker=dset.masker,
      metadata_df=dset.metadata,
      out_dir=out_dir,
      overwrite=True)
    dset.images = temp_images
    
    dset = ImagesToCoordinates(
      merge_strategy="replace", 
      z_threshold=z_threshold, 
      remove_subpeaks=remove_subpeaks, 
      two_sided=two_sided,
      min_distance=min_distance).transform(dset)
    dset.save(os.path.join(out_dir, f"{prefix}_dset.pklz"))
    ale = ALE()

    cbma = ale.fit(dset)
    cbma.save_maps(output_dir=out_dir, prefix=prefix)

    return os.path.join(out_dir, f"{prefix}_z.nii.gz")

