import bpy
import io
import math
import mathutils
import struct
from contextlib import redirect_stdout

# math constants

rad90 = math.radians(90)
rad180 = math.radians(180)
rad360 = math.radians(360)
rad720 = math.radians(720)

# file reading

u8CodeB = ">B"
i8CodeB = ">b"
u16CodeB = ">H"
i16CodeB = ">h"
u32CodeB = ">L"
i32CodeB = ">l"
fpCodeB = ">f"
u8CodeL = "<B"
i8CodeL = "<b"
u16CodeL = "<H"
i16CodeL = "<h"
u32CodeL = "<L"
i32CodeL = "<l"
fpCodeL = "<f"

# old games are big and new ones are little, so assume little as default
def readAndParseInt(inFile,bytes,signed=False,endian="little"):
	if endian == "big":
		return readAndParseIntBig(infile,bytes,signed)
	if bytes == 1:
		parseString = i8CodeL if signed else u8CodeL
	elif bytes == 2:
		parseString = i16CodeL if signed else u16CodeL
	elif bytes == 4:
		parseString = i32CodeL if signed else u32CodeL
	else:
		raise ValueException("invalid int bytesize: "+str(bytes))
	return struct.unpack(parseString,inFile.read(struct.calcsize(parseString)))[0]
def readAndParseIntBig(inFile,bytes,signed=False):
	if bytes == 1:
		parseString = i8CodeB if signed else u8CodeB
	elif bytes == 2:
		parseString = i16CodeB if signed else u16CodeB
	elif bytes == 4:
		parseString = i32CodeB if signed else u32CodeB
	else:
		raise ValueException("invalid int bytesize: "+str(bytes))
	return struct.unpack(parseString,inFile.read(struct.calcsize(parseString)))[0]

def readAndParseFloat(inFile,endian="little"):
	if endian == "big":
		return readAndParseFloatBig(infile)
	return struct.unpack(fpCodeL,inFile.read(struct.calcsize(fpCodeL)))[0]
def readAndParseFloatBig(inFile):
	return struct.unpack(fpCodeB,inFile.read(struct.calcsize(fpCodeB)))[0]

def readStr(inFile):
	strBytes = b""
	c = inFile.read(1)
	while c != b"\x00" and c != b"":
		strBytes += c
		c = inFile.read(1)
	return strBytes.decode("utf-8")
def readFixedLenStr(inFile,length):
	strBytes = b""
	for i in range(length):
		c = inFile.read(1)
		strBytes += c
	return strBytes.decode("utf-8")

# Blender helper functions

def flipRoll(roll):
	return roll % rad360 - rad180

def clampRoll(roll,angleEpsilon):
	# limits roll to being between -180 and +180
	while roll > rad180: roll -= rad180
	while roll < -rad180: roll += rad180
	if abs(roll) < angleEpsilon:
		roll = 0
	return roll

def clampBoneRoll(editBone,angleEpsilon):
	editBone.roll = clampRoll(editBone.roll,angleEpsilon)

def mirrorBone(editBone,otherBone):
	# replaces editBone's position and rotation with a mirrored version of otherBone's
	roll = editBone.roll
	editBone.matrix = otherBone.matrix @ mathutils.Matrix([[-1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
	editBone.head = otherBone.head * mathutils.Vector((-1,1,1))
	editBone.tail = otherBone.tail * mathutils.Vector((-1,1,1))
	editBone.roll = -otherBone.roll

def isBonePairIdentical(thisBone,otherBone,positionEpsilon,angleEpsilon,mirrorable=False):
	# the logic: would the one bone equal the other bone within epsilon?
	# the metrics are head position, angle between Y-axes (facing direction), and angle between Z-axes (roll)
	pos1 = thisBone.head
	pos2 = otherBone.head
	if mirrorable:
		pos1 = pos1 * mathutils.Vector((-1,1,1))
	for p in range(3):
		posDiff = abs(pos1[p] - pos2[p])
		if posDiff >= positionEpsilon:
			return False,"position["+str(p)+"] diff. of "+str(posDiff)+" (out of tolerance by "+str(positionEpsilon-posDiff)+")"
	vector1 = thisBone.y_axis
	vector2 = otherBone.y_axis
	if mirrorable:
		vector1 = vector1 @ mathutils.Matrix([[-1,0,0],[0,1,0],[0,0,1]])
	angleDiff = vector1.angle(vector2)
	if mirrorable:
		if angleDiff > rad90: angleDiff = abs(rad180 - angleDiff) # both "0 degrees apart" and "180 degrees apart" are correct for mirroring (to account for potential flipping)
	if (angleDiff >= angleEpsilon):
		return False,"facing vector angle diff. of "+str(math.degrees(angleDiff))+"d (out of tolerance by "+str(math.degrees(angleEpsilon-angleDiff))+"d)"
	vector1 = thisBone.z_axis
	vector2 = otherBone.z_axis
	if mirrorable:
		vector1 = vector1 @ mathutils.Matrix([[-1,0,0],[0,1,0],[0,0,1]])
	angleDiff = vector1.angle(vector2)
	if mirrorable:
		if angleDiff > rad90: angleDiff = abs(rad180 - angleDiff) # same as above
	if (angleDiff >= angleEpsilon):
		return False,"roll angle diff. of "+str(math.degrees(angleDiff))+"d (out of tolerance by "+str(math.degrees(angleEpsilon-angleDiff))+"d)"
	return True,""

def create_armature_from_bones(boneList,name,boneSize,positionEpsilon,angleEpsilon):
	bpy.ops.object.select_all(action="DESELECT")
	bpy.ops.object.armature_add(enter_editmode=True, align="WORLD", location=(0,0,0), rotation=(0,0,0), scale=(1,1,1))
	skelObj = bpy.context.view_layer.objects.active
	skeleton = skelObj.data
	skeleton.show_names = True
	# delete the default bone to start with
	bpy.ops.armature.select_all(action="SELECT")
	bpy.ops.armature.delete()
	# start adding
	editBones = skeleton.edit_bones
	for b in boneList:
		# assumption: no bone will ever precede its parent (i.e. the parent will always be there already to attach to, no second pass needed)
		newBone = editBones.new(b.getName())
		newBone.length = boneSize
		newBone.parent = editBones[b.getParent()] if b.getParent() != 0xffff else None
		parentMatrix = newBone.parent.matrix if newBone.parent else mathutils.Matrix.Identity(4)
		posMatrix = mathutils.Matrix.Translation(b.getPosition())
		rotMatrix = mathutils.Quaternion(b.getRotation()).to_matrix()
		rotMatrix.resize_4x4()
		newBone.matrix = parentMatrix @ (posMatrix @ rotMatrix)
		newBone.length = boneSize # have seen odd non-rounding when not doing this
		# put "normal" bones in layer 1 and endpoints in layer 2
		# must be done in this order or the [0] set will be dropped because bones must be in at least one layer
		newBone.layers[1] = b.isEndpoint()
		newBone.layers[0] = not b.isEndpoint()
	# now that the bones are in, spin them around so they point in a more logical-for-Blender direction
	for b in editBones:
		b.transform(mathutils.Euler((math.radians(90),0,0)).to_matrix()) # transform from lying down (+Y up +Z forward) to standing up (+Z up -Y forward)
		roll = b.y_axis # roll gets lost after the following matrix mult for some reason, so preserve it
		b.matrix = b.matrix @ mathutils.Matrix([[0,1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]]) # change from +X being the "main axis" to +Y
		b.align_roll(roll)
		# everything done, now apply epsilons
		b.head = [(0 if abs(p) < positionEpsilon else p) for p in b.head]
		b.tail = [(0 if abs(p) < positionEpsilon else p) for p in b.tail]
		clampBoneRoll(b,angleEpsilon)
	skelObj.name = name
	skelObj.data.name = name
	bpy.ops.armature.select_all(action="DESELECT")
	bpy.ops.object.mode_set(mode="OBJECT")
	return skelObj # return the new object

def cleanup_mesh(context,meshObj,looseVerts,emptyGroups,emptyShapes):
	tempActive = context.view_layer.objects.active
	context.view_layer.objects.active = meshObj
	meshData = meshObj.data
	# remove all the vertices without faces attached (there can be a lot and it's apparently hard to do in any other way)
	if looseVerts:
		bpy.ops.object.mode_set(mode="EDIT")
		with redirect_stdout(io.StringIO()): # hide "X verts deleted" output
			bpy.ops.mesh.delete_loose(use_verts=True,use_edges=False,use_faces=False)
		bpy.ops.object.mode_set(mode="OBJECT")
	# clean up vertex groups that have nothing in them
	if emptyGroups:
		unusedVertexGroups = [g.name for g in meshObj.vertex_groups]
		for v in meshData.vertices:
			for g in v.groups:
				try: unusedVertexGroups.remove(meshObj.vertex_groups[g.group].name)
				except ValueError: pass
		for g in unusedVertexGroups:
			meshObj.vertex_groups.remove(meshObj.vertex_groups[g])
	# determine which shapes don't do anything and remove them
	# seems to be somewhat conservative (some shapes with no visible effect are kept), but that's the safer error to make
	if emptyShapes:
		keysToRemove = []
		for s in meshData.shape_keys.key_blocks:
			if s.name == "basis": continue
			isEmpty = True
			for v in range(len(meshData.vertices)):
				if meshData.vertices[v].co != s.data[v].co:
					isEmpty = False
			if isEmpty:
				keysToRemove.append(s)
		for r in keysToRemove:
			meshObj.shape_key_remove(r)
	context.view_layer.objects.active = tempActive

# Forge classes, because just packing/unpacking arrays gets old and error-prone

class MonadoForgeBone:
	def __init__(self):
		self._name = "Bone"
		self._parent = -1
		self._position = [0,0,0,1] # x, y, z, w
		self._rotation = [1,0,0,0] # w, x, y, z
		self._scale = [1,1,1,1] # x, y, z, w
		self._endpoint = False
	
	def getName(self):
		return self._name
	def setName(self,x):
		if not isinstance(x,str):
			raise TypeError("expected a string, not a(n) "+str(type(x)))
		self._name = x
	
	def getParent(self):
		return self._parent
	def clearParent(self):
		self._parent = -1
	def setParent(self,x):
		if not isinstance(x,int):
			raise TypeError("expected an int, not a(n) "+str(type(x)))
		self._parent = x
	
	def getPosition(self):
		return self._position
	def setPosition(self,a):
		if len(a) != 4:
			raise ValueError("sequence must be length 4, not "+str(len(a)))
		self._position = a[:]
	
	def getRotation(self):
		return self._rotation
	def setRotation(self,a):
		if len(a) != 4:
			raise ValueError("sequence must be length 4, not "+str(len(a)))
		self._rotation = a[:]
	
	def getScale(self):
		return self._scale
	def setScale(self,a):
		if len(a) != 4:
			raise ValueError("sequence must be length 4, not "+str(len(a)))
		self._scale = a[:]
	
	def isEndpoint(self):
		return self._endpoint
	def setEndpoint(self,x):
		if not isinstance(x,bool):
			raise TypeError("expected a bool, not a(n) "+str(type(x)))
		self._endpoint = x

class MonadoForgeSkeleton:
	def __init__(self):
		self._bones = []
	
	def getBones(self):
		return self._bones
	def clearBones(self):
		self._bones = []
	def addBone(self,bone):
		if not isinstance(bone,MonadoForgeBone):
			raise TypeError("expected a MonadoForgeBone, not a(n) "+str(type(bone)))
		self._bones.append(bone)
	def setBones(self,bones):
		self.clearBones()
		for b in bones: self.addBone(b)

class MonadoForgeVertex:
	def __init__(self):
		self._id = -1
		self._position = [0,0,0] # having position ever be None seems to cause Problems
		self._uvs = {}
		self._normal = None
		self._colour = None
		self._weightSetIndex = -1 # pre-bake
		self._weights = {} # post-bake (must also be by index rather than name sicne we don't necessarily know names)
	
	def getID(self):
		return self._id
	# only set by the parent mesh
	
	def getPosition(self):
		return self._position
	def setPosition(self,a):
		if len(a) != 3:
			raise ValueError("sequence must be length 3, not "+str(len(a)))
		self._position = a[:]
	# there is no "clearPosition" because of the None problem
	
	def hasUVs(self):
		return self._uvs != {}
	def getUVs(self):
		return self._uvs
	def getUV(self,layer):
		return self._uvs[layer]
	def clearUVs(self):
		self._uvs = {}
	def setUV(self,layer,value):
		if len(value) != 2:
			raise ValueError("sequence must be length 2, not "+str(len(value)))
		self._uvs[layer] = value
	
	def hasNormal(self):
		return self._normal != None
	def getNormal(self):
		return self._normal
	def clearNormal(self):
		self._normal = None
	def setNormal(self,a):
		if len(a) != 3:
			raise ValueError("sequence must be length 3, not "+str(len(a)))
		self._normal = a[:]
	
	def hasColour(self):
		return self._colour != None
	def getColour(self):
		return self._colour
	def clearColour(self):
		self._colour = None
	def setColour(self,a):
		if len(a) != 4: # allow alpha colours
			raise ValueError("sequence must be length 4, not "+str(len(a)))
		self._colour = a[:]
	
	def hasWeightIndex(self):
		return self._weightSetIndex != -1
	def getWeightSetIndex(self):
		return self._weightSetIndex
	def clearWeightSetIndex(self):
		self._weightSetIndex = -1
	def setWeightSetIndex(self,x):
		if not isinstance(x,int):
			raise TypeError("expected an int, not a(n) "+str(type(x)))
		self._weightSetIndex = x
	
	def hasWeights(self):
		return self._weights != {}
	def getWeights(self):
		return self._weights
	def getWeight(self,groupIndex):
		return self._weights[groupIndex]
	def clearWeights(self):
		self._weights = {}
	def setWeight(self,groupIndex,value):
		if not isinstance(groupIndex,int):
			raise TypeError("expected an int, not a(n) "+str(type(groupIndex)))
		if not isinstance(value,float):
			raise TypeError("expected a float, not a(n) "+str(type(value)))
		self._weights[groupIndex] = value

class MonadoForgeFace:
	def __init__(self):
		self._vertexIndexes = []
		self._materialIndex = 0
	
	def getVertexIndexes(self):
		return self._vertexIndexes
	def clearVertexIndexes(self):
		self._vertexIndexes = []
	def addVertexIndex(self,v):
		if not isinstance(v,int):
			raise TypeError("expected an int, not a(n) "+str(type(v)))
		self._vertexIndexes.append(v)
	def setVertexIndexes(self,a):
		if not isinstance(a,list):
			raise TypeError("expected a list, not a(n) "+str(type(a)))
		self._vertexIndexes = a[:]

class MonadoForgeMeshShape:
	def __init__(self):
		self._vtIndex = 0
		self._vertices = {} # indexes are not necessarily in order or sequential, so must be a dict (by index) rather than a plain list
		self._name = ""
	
	def getVertexTableIndex(self):
		return self._vtIndex
	def setVertexTableIndex(self,i):
		self._vtIndex = i
	
	def getVertices(self):
		return self._vertices
	def clearVertices(self):
		self._vertices = {}
	def addVertex(self,i,v):
		self._vertices[i] = v
	def setVertices(self,a):
		self._vertices = a
	
	def getName(self):
		return self._name
	def setName(self,x):
		if not isinstance(x,str):
			raise TypeError("expected a string, not a(n) "+str(type(x)))
		self._name = x

class MonadoForgeMesh:
	def __init__(self):
		self._name = "Mesh"
		self._vertices = []
		self._faces = []
		self._weightSets = {} # because it can be convenient to hold these here and have vertexes just refer with index
		self._shapes = [] # list of MonadoForgeMeshShapes
	
	def getVertices(self):
		return self._vertices
	def clearVertices(self):
		self._vertices = []
	def addVertex(self,v):
		if not isinstance(v,MonadoForgeVertex):
			raise TypeError("expected a MonadoForgeVertex, not a(n) "+str(type(v)))
		self._vertices.append(v)
	def setVertices(self,a):
		self._vertices = []
		for v in a: self.addVertex(v)
	
	def getFaces(self):
		return self._faces
	def clearFaces(self):
		self._faces = []
	def addFace(self,f):
		if not isinstance(f,MonadoForgeFace):
			raise TypeError("expected a MonadoForgeFace, not a(n) "+str(type(f)))
		self._faces.append(f)
	def setFaces(self,a):
		self._faces = []
		for f in a: self.addFace(f)
	
	def getWeightSets(self):
		return self._weightSets
	def clearWeightSets(self):
		self._weightSets = []
	def addWeightSet(self,index,a):
		if not isinstance(a,list):
			raise TypeError("expected a list, not a(n) "+str(type(a)))
		self._weightSets[index] = a
	def setWeightSets(self,d):
		if not isinstance(d,dict):
			raise TypeError("expected a dict, not a(n) "+str(type(d)))
		self._weightSets = d
	
	def getShapes(self):
		return self._shapes
	def clearShapes(self):
		self._shapes = []
	def addShape(self,shape):
		if not isinstance(shape,MonadoForgeMeshShape):
			raise TypeError("expected a MonadoForgeMeshShape, not a(n) "+str(type(shape)))
		self._shapes.append(shape)
	def setShapes(self,shapeList):
		self._shapes = []
		for s in shapeList: self.addShape(s)
	
	# assumption: if a single vertex has any of these, all the other vertices must also
	def hasUVs(self):
		for v in self._vertices:
			if v.hasUVs(): return True
		return False
	def hasNormals(self):
		for v in self._vertices:
			if v.hasNormal(): return True
		return False
	def hasColours(self):
		for v in self._vertices:
			if v.hasColour(): return True
		return False
	def hasWeightIndexes(self):
		for v in self._vertices:
			if v.hasWeightIndex(): return True
		return False
	def hasWeights(self):
		for v in self._vertices:
			if v.hasWeights(): return True
		return False
	def hasShapes(self):
		return len(self._shapes) > 0
	
	def indexVertices(self):
		for i,v in enumerate(self._vertices):
			v._id = i
	
	def getVertexPositionsList(self):
		return [v.getPosition() for v in self._vertices]
	def getUVLayerList(self):
		layers = []
		for v in self._vertices:
			layers += [k for k in v.getUVs().keys()]
		return list(set(layers))
	def getVertexUVsLayer(self,layer):
		return [v.getUVs()[layer] for v in self._vertices]
	def getVertexNormalsList(self):
		return [v.getNormal() for v in self._vertices]
	def getVertexColoursList(self):
		return [v.getColour() for v in self._vertices]
	def getVertexWeightIndexesList(self):
		return [v.getWeightSetIndex() for v in self._vertices]
	def getVertexWeightsList(self):
		return [v.getWeights() for v in self._vertices]
	def getVertexesInWeightGroup(self,groupID):
		return [v for v in self._vertices if groupID in v.getWeights().keys()]
	def getFaceVertexIndexesList(self):
		return [f.getVertexIndexes() for f in self._faces]

class MonadoForgeMeshHeader:
	# intended to be immutable, so all the setting is in the constructor
	def __init__(self,id,md,vt,ft,mm,lod):
		self._meshID = id
		self._meshFlags = md
		self._meshVertTableIndex = vt
		self._meshFaceTableIndex = ft
		self._meshMaterialIndex = mm
		self._meshLODValue = lod
	def getMeshID(self):
		return self._meshID
	def getMeshFlags(self):
		return self._meshFlags
	def getMeshVertTableIndex(self):
		return self._meshVertTableIndex
	def getMeshFaceTableIndex(self):
		return self._meshFaceTableIndex
	def getMeshMaterialIndex(self):
		return self._meshMaterialIndex
	def getMeshLODValue(self):
		return self._meshLODValue

# this class is specifically for passing wimdo results to wismt import
# assumption: there can be only one skeleton (it's just a collection of bones technically)
class MonadoForgeWimdoPackage:
	def __init__(self,skel,mh,sh):
		if not isinstance(skel,MonadoForgeSkeleton):
			raise TypeError("expected a MonadoForgeSkeleton, not a(n) "+str(type(skel)))
		if not isinstance(mh,list):
			raise TypeError("expected a list, not a(n) "+str(type(mh)))
		if not isinstance(sh,list):
			raise TypeError("expected a list, not a(n) "+str(type(sh)))
		self._skeleton = skel
		self._meshHeaders = mh
		self._shapeHeaders = sh
	def getSkeleton(self):
		return self._skeleton
	def getMeshHeaders(self):
		return self._meshHeaders
	def getShapeHeaders(self):
		return self._shapeHeaders
	
	def getLODList(self):
		lods = []
		for mh in self._meshHeaders:
			lods.append(mh.getMeshLODValue())
		return list(set(lods))
	def getBestLOD(self):
		return min(self.getLODList())

# this is intended to be used only once everything game-specific is done and the data is fully in agnostic format
class MonadoForgeImportedPackage:
	def __init__(self):
		self._skeletons = []
		self._meshes = []
	
	def getSkeletons(self):
		return self._skeletons
	def clearSkeletons(self):
		self._skeletons = []
	def addSkeleton(self,skeleton):
		self._skeletons.append(skeleton)
	def setSkeletons(self,skeletons):
		self._skeletons = skeletons[:]
	
	def getMeshes(self):
		return self._meshes
	def clearMeshes(self):
		self._meshes = []
	def addMesh(self,mesh):
		self._meshes.append(mesh)
	def setMeshes(self,meshes):
		self._meshes = meshes[:]

def register():
	pass

def unregister():
	pass

#[...]