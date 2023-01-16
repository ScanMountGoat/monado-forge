# Monado Forge
An addon for Blender (written with 3.3.1) for working with Xenoblade files. Adds a tab in the 3D view's right-hand toolbox with a bunch of useful features.

**General notice:** Keep the system console toggled on so you can see any potential warnings.

## Game support
* :x: - Not supported, but planned (eventually).
* :hash: - Partially supported; number is a basic "how done does this feel" estimate.
* :o: - Not well-tested (if at all). _Ought_ to work just as well as the best-supported version, but no guarantees.
* :heavy_check_mark: - Supported.

| | <img alt="XC1" src="https://www.xenoserieswiki.org/w/images/8/8d/Article_icon_-_Xenoblade_Chronicles.svg" width="24px"/> | <img alt="XCX" src="https://www.xenoserieswiki.org/w/images/3/3f/Article_icon_-_Xenoblade_Chronicles_X.svg" width="24px"/> | <img alt="XC2" src="https://www.xenoserieswiki.org/w/images/a/a8/Article_icon_-_Xenoblade_Chronicles_2.svg" width="24px"/> | <img alt="XC1DE" src="https://www.xenoserieswiki.org/w/images/6/6f/Article_icon_-_Xenoblade_Chronicles_Definitive_Edition.svg" width="24px"/> | <img alt="XC3" src="https://www.xenoserieswiki.org/w/images/b/bc/Article_icon_-_Xenoblade_Chronicles_3.svg" width="24px"/>
| --- | :---: | :---: | :---: | :---: | :---: |
| Skeleton import | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| Model import | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Vertex colours | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ UVs | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Vertex normals | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Vertex groups | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Shapes/Morphs | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Textures | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | 10% |
| └ Materials | :x: | :x: | :x: | :x: | :x: |

## Current features
### Skeleton
* Imports skeletons from .arc and .chr files.
* Controllable epsilon, for choosing whether 0.00001 should just be set to 0, and whether a pair of bones that differ by only that much should be treated as equal. Applies to position and rotation separately.
* Choose whether to also import endpoints as bones, and puts them in a second bone layer.
* One-click flipping and mirroring bones so _L and _R sides match. Auto-mirror skips bones that seem like they might be intentionally uneven.
* Select individual bones for manual flipping/mirroring.
* One-click renaming bones to move the _L/_R to the end, instead of sitting in the middle.
* Merge two armatures, keeping only one copy of bones with the same name. Supports both "merge all" and "merge only if similar enough".

### Model
* Imports .wimdo/.wismt model files. The .wimdo can be imported alone, which grabs only whatever bones are inside, while the .wismt import requires a .wimdo to go with it.
* Supports normals, UVs, vertex colours, rigging (vertex groups), and shapes (morphs). Models are automatically parented to the skeleton found in the .wimdo.
* Optionally also import lower-LOD models. Doesn't currently distinguish them in any way.
* Optional mesh cleanup, erasing unused vertices, vertex groups, and shapes.
* Imports textures and saves them to a specified folder. By default, keeps only the biggest of each, but provides the option to keep all resolutions (using subfolders). Supports all known-to-be-used formats (R8G8B8A8, BC1, BC3, BC4, BC5, BC7).
* Optionally assumes that BC5 textures are normal maps, and auto-calculates the blue channel for them.

## Known issues
### Things with workarounds
* The workflow for getting the proper skeleton setup is not the best. You have to import the .arc/.chr, then import the .wimdo+.wismt, and then use the skeleton merge feature to merge the .wimdo+.wismt skeleton into the .arc/.chr one. There's improvement to be made, but it works well enough and there are more important features to focus on.
* Some models have multiple weight tables, but the information about which one to use per each mesh cannot yet be found. Use the "Weight Table Override" feature to select which one to use for all meshes, and re-import for each one so you can pick-and-choose which ones are correct.
### Things with no workarounds
* Blender does not support per-shape normals, so that information is lost. In theory it won't matter much.
* Models entirely embedded in the .wimdo are not checked for yet. Very rare, so ought not to be a big deal.
* Models without skeletons will probably not import correctly. Should be an easy fix, but still counts as a "known issue".
* Outline meshes are not recognised or treated as anything special. If you get two entirely identical meshes, consider that one may be the outline, in which case you can delete one of them (probably the higher-numbered one). Unclear how to handle this as of yet (guessing it's material-related).
* Outline data is not yet processed. Not quite sure how to be honest, perhaps will leverage a vertex colour layer for it.

## Planned features
Roughly in order of priority.
* (XC3) Getting textures from external folders
* Better console feedback for super-long-running operations but without too many lines being printed
* UV folding
* Material assignment

