import bpy
import math
import mathutils
import os
import traceback
from bpy.props import (
						BoolProperty,
						FloatProperty,
						IntProperty,
						PointerProperty,
						StringProperty,
						)
from bpy.types import (
						Operator,
						Panel,
						PropertyGroup,
						)

from . classes import *
from . utils import *
from . import_funcs import *

class MonadoForgeViewImportSkeletonOperator(Operator):
	bl_idname = "object.monado_forge_skeleton_import_operator"
	bl_label = "Xenoblade Skeleton Import Operator"
	bl_description = "Imports a skeleton from a Xenoblade file"
	bl_options = {"REGISTER","UNDO"}
	
	@classmethod
	def poll(cls, context):
		return context.scene.monado_forge_import.skeletonPath
	
	def execute(self, context):
		try:
			game = context.scene.monado_forge_main.game
			printProgress = context.scene.monado_forge_main.printProgress
			absolutePath = bpy.path.abspath(context.scene.monado_forge_import.skeletonPath)
			if printProgress:
				print("Importing skeleton from: "+absolutePath)
			
			filename, fileExtension = os.path.splitext(absolutePath)
			expectedExtension = {"XC1":".brres","XCX":".xcx","XC2":".arc","XC1DE":".chr","XC3":".chr",}[game]
			if fileExtension != expectedExtension:
				self.report({"ERROR"}, "Unexpected file type (for "+game+", expected "+expectedExtension+")")
				return {"CANCELLED"}
			
			# first, read in the data and store it in a game-agnostic way
			if game == "XC1": # big endian
				modelFormat = "BRES"
			elif game == "XCX": # big endian
				modelFormat = "[xcx]"
			elif game == "XC2":
				modelFormat = "SAR1"
			elif game == "XC1DE":
				modelFormat = "SAR1"
			elif game == "XC3":
				modelFormat = "SAR1"
			
			if modelFormat == "BRES":
				self.report({"ERROR"}, ".brres format not yet supported")
				return {"CANCELLED"}
			elif modelFormat == ".xcx":
				self.report({"ERROR"}, "(whatever XCX uses) format not yet supported")
				return {"CANCELLED"}
			elif modelFormat == "SAR1":
				return import_sar1_skeleton_only(self, context)
			else:
				self.report({"ERROR"}, "Unknown format: "+modelFormat)
				return {"CANCELLED"}
			
		except Exception:
			traceback.print_exc()
			self.report({"ERROR"}, "Unexpected error; see console")
			return {"CANCELLED"}
		return {"FINISHED"}

class MonadoForgeViewImportModelOperator(Operator):
	bl_idname = "object.monado_forge_model_import_operator"
	bl_label = "Xenoblade Model Import Operator"
	bl_description = "Imports a model from a Xenoblade file"
	bl_options = {"REGISTER","UNDO"}
	
	@classmethod
	def poll(cls, context):
		# can't import a .wismt without a .wimdo (requires vertex table + face table alignment)
		return context.scene.monado_forge_import.singlePath or context.scene.monado_forge_import.defsPath
	
	def execute(self, context):
		game = context.scene.monado_forge_main.game
		# this isn't part of the poll because it's not a trivial check and the fix needs to be more descriptive
		if context.scene.monado_forge_import.autoSaveTextures:
			if not os.path.isdir(bpy.path.abspath(context.scene.monado_forge_import.texturePath)):
				self.report({"ERROR"}, "Auto-save selected, but texture output path is not an existing folder")
				return {"CANCELLED"}
		if game == "XC3" and not (os.path.isdir(bpy.path.abspath(context.scene.monado_forge_import.textureRepoMPath)) and os.path.isdir(bpy.path.abspath(context.scene.monado_forge_import.textureRepoHPath))):
			self.report({"ERROR"}, "Import uncached textures selected, but no texture repositories provided (both are required)")
			return {"CANCELLED"}
		try:
			if game == "XC1" or game == "XCX":
				self.report({"ERROR"}, "game not yet supported")
				return {"CANCELLED"}
			if context.scene.monado_forge_import.defsPath and context.scene.monado_forge_import.dataPath:
				return import_wimdo_and_wismt(self, context)
			elif context.scene.monado_forge_import.defsPath:
				return import_wimdo_only(self, context)
			self.report({"ERROR"}, "Unexpected error; code shouldn't be able to reach here")
			return {"CANCELLED"}
		except Exception:
			traceback.print_exc()
			self.report({"ERROR"}, "Unexpected error; see console")
			return {"CANCELLED"}

class MonadoForgeViewImportModelWithSkeletonOperator(Operator):
	bl_idname = "object.monado_forge_model_with_skeleton_import_operator"
	bl_label = "Xenoblade Model With Skeleton Import Operator"
	bl_description = "Imports a model using an external skeleton from a Xenoblade file"
	bl_options = {"REGISTER","UNDO"}
	
	@classmethod
	def poll(cls, context):
		# require all of .arc/.chr, .wimdo, and .wismt (there are no known situations where a .wimdo with an embedded model has a .arc/.chr but no .wismt)
		return context.scene.monado_forge_import.singlePath or (context.scene.monado_forge_import.skeletonPath and context.scene.monado_forge_import.defsPath and context.scene.monado_forge_import.dataPath)
	
	def execute(self, context):
		game = context.scene.monado_forge_main.game
		# this isn't part of the poll because it's not a trivial check and the fix needs to be more descriptive
		if context.scene.monado_forge_import.autoSaveTextures:
			if not os.path.isdir(bpy.path.abspath(context.scene.monado_forge_import.texturePath)):
				self.report({"ERROR"}, "Auto-save selected, but texture output path is not an existing folder")
				return {"CANCELLED"}
		if game == "XC3" and not (os.path.isdir(bpy.path.abspath(context.scene.monado_forge_import.textureRepoMPath)) and os.path.isdir(bpy.path.abspath(context.scene.monado_forge_import.textureRepoHPath))):
			self.report({"ERROR"}, "Import uncached textures selected, but no texture repositories provided (both are required)")
			return {"CANCELLED"}
		
		filename, fileExtension = os.path.splitext(bpy.path.abspath(context.scene.monado_forge_import.skeletonPath))
		expectedExtension = {"XC1":".brres","XCX":".xcx","XC2":".arc","XC1DE":".chr","XC3":".chr",}[game]
		if fileExtension != expectedExtension:
			self.report({"ERROR"}, "Unexpected file type (for "+game+", expected "+expectedExtension+")")
			return {"CANCELLED"}
		
		try:
			if game == "XC1" or game == "XCX":
				self.report({"ERROR"}, "game not yet supported")
				return {"CANCELLED"}
			return import_sar1_skel_and_wimdo_and_wismt(self, context)
			self.report({"ERROR"}, "Unexpected error; code shouldn't be able to reach here")
			return {"CANCELLED"}
		except Exception:
			traceback.print_exc()
			self.report({"ERROR"}, "Unexpected error; see console")
			return {"CANCELLED"}

class MonadoForgeViewImportCleanupModelOperator(Operator):
	bl_idname = "object.monado_forge_cleanup_model_operator"
	bl_label = "Xenoblade Model Cleanup Operator"
	bl_description = "Does selected cleanup operations to all selected meshes"
	bl_options = {"REGISTER","UNDO"}
	
	@classmethod
	def poll(cls, context): # must have at least one mesh selected
		activeObject = context.view_layer.objects.active
		selectedObjects = context.view_layer.objects.selected
		if activeObject and activeObject.type == "MESH": return True
		for s in selectedObjects:
			if s.type == "MESH": return True
		return False
	
	def execute(self, context):
		try:
			objList = []
			activeObject = context.view_layer.objects.active
			selectedObjects = context.view_layer.objects.selected
			if activeObject and activeObject.type == "MESH":
				objList.append(activeObject)
			for s in selectedObjects:
				if s.type == "MESH":
					objList.append(s)
			for obj in objList:
				cleanup_mesh(context,obj,context.scene.monado_forge_import.cleanupLooseVertices,context.scene.monado_forge_import.cleanupEmptyGroups,context.scene.monado_forge_import.cleanupEmptyShapes)
			return {"FINISHED"}
		except Exception:
			traceback.print_exc()
			self.report({"ERROR"}, "Unexpected error; see console")
			return {"CANCELLED"}

class MonadoForgeViewImportProperties(PropertyGroup):
	skeletonPath : StringProperty(
		name="Skeleton Path",
		description="File to import",
		default="",
		maxlen=1024,
		subtype="FILE_PATH",
	)
	boneSize : FloatProperty(
		name="Bone Size",
		description="Length of bones",
		default=0.1,
		min=0.01,
		soft_min=0.01,
		soft_max=10,
		unit="LENGTH",
	)
	importEndpoints : BoolProperty(
		name="Also Import Endpoints",
		description="Imports endpoints as well and adds them to the skeleton (in layer 2)",
		default=False,
	)
	singlePath : StringProperty(
		name="Path",
		description="File to import",
		default="",
		maxlen=1024,
		subtype="FILE_PATH",
	)
	defsPath : StringProperty(
		name="Definition Path",
		description="Definitions file to import",
		default="",
		maxlen=1024,
		subtype="FILE_PATH",
	)
	dataPath : StringProperty(
		name="Data Path",
		description="Data file to import",
		default="",
		maxlen=1024,
		subtype="FILE_PATH",
	)
	textureRepoMPath : StringProperty(
		name=r"\m\ Path",
		description=r"Path to \m\ texture repository",
		default="",
		maxlen=1024,
		subtype="FILE_PATH",
	)
	textureRepoHPath : StringProperty(
		name=r"\h\ Path",
		description=r"Path to \h\ texture repository",
		default="",
		maxlen=1024,
		subtype="FILE_PATH",
	)
	tempWeightTableOverride : IntProperty(
		name="Weight Table Override",
		description="Force all meshes to use this weight table (see readme for explanation)",
		default=0,
		min=0,
	)
	alsoImportLODs : BoolProperty(
		name="Also Import LODs",
		description="Include lower-detail meshes in the import",
		default=False,
	)
	doCleanupOnImport : BoolProperty(
		name="Clean Up After Import",
		description="Perform selected cleanup tasks once import is complete",
		default=True,
	)
	importUncachedTextures : BoolProperty(
		name="Import Uncached Textures",
		description="Uncheck to skip importing the large and slow textures",
		default=True,
	)
	autoSaveTextures : BoolProperty(
		name="Auto-Save Textures",
		description="Save extracted textures to disk",
		default=True,
	)
	texturePath : StringProperty(
		name="Texture Output Path",
		description="Folder where textures will be auto-saved to (WARNING: will overwrite existing!)",
		default="",
		maxlen=1024,
		subtype="FILE_PATH",
	)
	createDummyShader : BoolProperty(
		name="Create Dummy Shader",
		description="Run new materials through a simple base-colour-only Principled BSDF (false: use an empty group node instead)",
		default=True,
	)
	cleanupLooseVertices : BoolProperty(
		name="Loose Vertices",
		description="Erase vertices not connected to anything",
		default=True,
	)
	cleanupEmptyGroups : BoolProperty(
		name="Empty Groups",
		description="Erase vertex groups with nothing using them",
		default=True,
	)
	cleanupEmptyShapes : BoolProperty(
		name="Empty Shapes",
		description="Erase shape keys that have no effect",
		default=False,
	)
	differentiateTextures : BoolProperty(
		name="Differentiate Image Names",
		description="Appends the filename to the start of texture names (so they don't overwrite existing ones)",
		default=True,
	)
	blueBC5 : BoolProperty(
		name="Normalize BC5s",
		description="Assume that BC5-format images are normal maps, and calculate the blue channel accordingly",
		default=True,
	)
	splitTemps : BoolProperty(
		name="Dechannelise \"temp\" Files",
		description="(warning: slow, thinking of a better way to implement the feature)\nIf the image is named \"temp0000\" or similar, splits it out into an independent file per channel",
		default=False,
	)
	keepAllResolutions : BoolProperty(
		name="Keep All Resolutions",
		description="Include all textures, even if there's a larger resolution of the same",
		default=False,
	)

class OBJECT_PT_MonadoForgeViewImportPanel(Panel):
	bl_idname = "OBJECT_PT_MonadoForgeViewImportPanel"
	bl_label = "Import"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_parent_id = "OBJECT_PT_MonadoForgePanel"

	def draw(self, context):
		layout = self.layout
		scn = context.scene
		col = layout.column(align=True)
		activeObject = bpy.context.view_layer.objects.active
		expectedSkeletonExtension = {"XC1":".brres","XCX":".xcx","XC2":".arc","XC1DE":".chr","XC3":".chr",}[scn.monado_forge_main.game]
		col.prop(scn.monado_forge_import, "skeletonPath", text=expectedSkeletonExtension)
		if scn.monado_forge_main.game == "XC1":
			col.prop(scn.monado_forge_import, "singlePath", text=".brres")
		else:
			defsRow = col.row()
			defsRow.prop(scn.monado_forge_import, "defsPath", text=".wimdo")
			dataRow = col.row()
			dataRow.prop(scn.monado_forge_import, "dataPath", text=".wismt")
		col.prop(scn.monado_forge_import, "importUncachedTextures")
		if scn.monado_forge_main.game == "XC3":
			texMRow = col.row()
			texMRow.prop(scn.monado_forge_import, "textureRepoMPath", text="\\m\\")
			texMRow.enabled = scn.monado_forge_import.importUncachedTextures
			texHRow = col.row()
			texHRow.prop(scn.monado_forge_import, "textureRepoHPath", text="\\h\\")
			texHRow.enabled = scn.monado_forge_import.importUncachedTextures
		col.prop(scn.monado_forge_import, "autoSaveTextures")
		texturePathRow = col.row()
		texturePathRow.prop(scn.monado_forge_import, "texturePath", text="...to")
		texturePathRow.enabled = scn.monado_forge_import.autoSaveTextures
		col.prop(scn.monado_forge_import, "createDummyShader")
		col.separator()
		col.operator(MonadoForgeViewImportSkeletonOperator.bl_idname, text="Import Skeleton Only", icon="IMPORT")
		col.operator(MonadoForgeViewImportModelOperator.bl_idname, text="Import Model Only", icon="IMPORT")
		col.operator(MonadoForgeViewImportModelWithSkeletonOperator.bl_idname, text="Import Model With Skeleton", icon="IMPORT")

class OBJECT_PT_MonadoForgeViewImportSkeletonOptionsPanel(Panel):
	bl_idname = "OBJECT_PT_MonadoForgeViewImportSkeletonOptionsPanel"
	bl_label = "Skeleton Import Options"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_parent_id = "OBJECT_PT_MonadoForgeViewImportPanel"
	
	def draw(self, context):
		layout = self.layout
		scn = context.scene
		col = layout.column(align=True)
		col.prop(scn.monado_forge_import, "boneSize")
		epSubcol = col.column()
		epSubcol.prop(scn.monado_forge_import, "importEndpoints")
		if scn.monado_forge_main.game == "XC1": # endpoints are just normal bones, conceptually always selected
			epSubcol.enabled = False

class OBJECT_PT_MonadoForgeViewImportModelOptionsPanel(Panel):
	bl_idname = "OBJECT_PT_MonadoForgeViewImportModelOptionsPanel"
	bl_label = "Model Import Options"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_parent_id = "OBJECT_PT_MonadoForgeViewImportPanel"
	
	def draw(self, context):
		layout = self.layout
		scn = context.scene
		col = layout.column(align=True)
		col.prop(scn.monado_forge_import, "tempWeightTableOverride")
		col.prop(scn.monado_forge_import, "alsoImportLODs")
		col.prop(scn.monado_forge_import, "doCleanupOnImport")
		col.operator(MonadoForgeViewImportCleanupModelOperator.bl_idname, text="Clean Up Selected Meshes", icon="BRUSH_DATA")

class OBJECT_PT_MonadoForgeViewImportTextureOptionsPanel(Panel):
	bl_idname = "OBJECT_PT_MonadoForgeViewImportTextureOptionsPanel"
	bl_label = "Texture Import Options"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_parent_id = "OBJECT_PT_MonadoForgeViewImportPanel"
	
	def draw(self, context):
		layout = self.layout
		scn = context.scene
		col = layout.column(align=True)
		col.prop(scn.monado_forge_import, "differentiateTextures")
		col.prop(scn.monado_forge_import, "blueBC5")
		col.prop(scn.monado_forge_import, "splitTemps")
		col.prop(scn.monado_forge_import, "keepAllResolutions")

class OBJECT_PT_MonadoForgeViewImportCleanupPanel(Panel):
	bl_idname = "OBJECT_PT_MonadoForgeViewImportCleanupPanel"
	bl_label = "Model Cleanup Options"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_parent_id = "OBJECT_PT_MonadoForgeViewImportModelOptionsPanel"
	
	def draw(self, context):
		layout = self.layout
		scn = context.scene
		col = layout.column(align=True)
		col.prop(scn.monado_forge_import, "cleanupLooseVertices")
		col.prop(scn.monado_forge_import, "cleanupEmptyGroups")
		col.prop(scn.monado_forge_import, "cleanupEmptyShapes")

classes = (
			MonadoForgeViewImportSkeletonOperator,
			MonadoForgeViewImportModelOperator,
			MonadoForgeViewImportModelWithSkeletonOperator,
			MonadoForgeViewImportCleanupModelOperator,
			MonadoForgeViewImportProperties,
			OBJECT_PT_MonadoForgeViewImportPanel,
			OBJECT_PT_MonadoForgeViewImportSkeletonOptionsPanel,
			OBJECT_PT_MonadoForgeViewImportModelOptionsPanel,
			OBJECT_PT_MonadoForgeViewImportTextureOptionsPanel,
			OBJECT_PT_MonadoForgeViewImportCleanupPanel,
			)

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)

	bpy.types.Scene.monado_forge_import = PointerProperty(type=MonadoForgeViewImportProperties)

def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
	del bpy.types.Scene.monado_forge_import

#[...]