# Monado Forge
An addon for Blender (written with 3.3.1) for working with Xenoblade files.

## Game support
* :x: - Not supported, but planned (eventually).
* :o: - Ought to work, but not well-tested (if at all).
* :heavy_check_mark: - Supported.

| | <img alt="XC1" src="https://www.xenoserieswiki.org/w/images/8/8d/Article_icon_-_Xenoblade_Chronicles.svg" width="24px"/> | <img alt="XCX" src="https://www.xenoserieswiki.org/w/images/3/3f/Article_icon_-_Xenoblade_Chronicles_X.svg" width="24px"/> | <img alt="XC2" src="https://www.xenoserieswiki.org/w/images/a/a8/Article_icon_-_Xenoblade_Chronicles_2.svg" width="24px"/> | <img alt="XC1DE" src="https://www.xenoserieswiki.org/w/images/6/6f/Article_icon_-_Xenoblade_Chronicles_Definitive_Edition.svg" width="24px"/> | <img alt="XC3" src="https://www.xenoserieswiki.org/w/images/b/bc/Article_icon_-_Xenoblade_Chronicles_3.svg" width="24px"/>
| --- | :---: | :---: | :---: | :---: | :---: |
| Skeleton import | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| Model import | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Vertex colours | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ UVs | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Vertex normals | :no_entry_sign: | :grey_question: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Vertex groups | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |
| └ Shapes/Morphs | :x: | :x: | :heavy_check_mark: | :heavy_check_mark: | :o: |

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
* Supports normals, UVs, vertex colours, rigging (vertex groups), and shapes (morphs). Models are automatically parented to the skeleton found in the .wimdo; use the skeleton merge feature to move it over to one imported from the matching .arc/.chr file.
* Optionally also import lower-LOD models. Doesn't currently distinguish them in any way.
* Optional mesh cleanup, erasing unused vertices, vertex groups, and shapes.

## Planned features
Roughly in order of priority.
* Texture extraction
* UV folding
* Material assignment

## Known issues
* Blender does not support per-shape normals, so that information is lost.
* Models entirely embedded in the .wimdo are not checked for yet.

