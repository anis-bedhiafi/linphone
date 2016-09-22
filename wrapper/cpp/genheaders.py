#!/usr/bin/python


import pystache
import genapixml as CApi
import abstractapi as AbsApi


class CppTranslator(object):
	def translate_enum(self, enum):
		enumDict = {}
		enumDict['name'] = enum.name.translate(self)
		enumDict['values'] = []
		i = 0
		for enumValue in enum.values:
			enumValDict = enumValue.translate(self)
			enumValDict['notLast'] = (i != len(enum.values)-1)
			enumDict['values'].append(enumValDict)
			i += 1
		return enumDict
	
	def translate_enum_value(self, enumValue):
		enumValueDict = {}
		enumValueDict['name'] = enumValue.name.translate(self)
		return enumValueDict
	
	def translate_class(self, _class):
		classDict = {}
		classDict['name'] = _class.name.translate(self)
		classDict['methods'] = []
		classDict['staticMethods'] = []
		for method in _class.instanceMethods:
			methodDict = self.translate_method(method)
			classDict['methods'].append(methodDict)
		for method in _class.classMethods:
			methodDict = self.translate_method(method)
			classDict['staticMethods'].append(methodDict)
		return classDict
	
	def translate_method(self, method):
		methodDict = {}
		methodDict['prototype'] = '{0} {1}();'.format(self.translate_type(method.returnType), method.name.translate(self))
		if method.type == AbsApi.Method.Type.Class:
			methodDict['prototype'] = 'static ' + methodDict['prototype'];
		return methodDict
	
	def translate_type(self, type):
		if type is not None:
			res = ''
			if type.isobject:
				if type.isconst:
					res += 'const '
				res += type.type.translate(self)
				res = 'std::shared_ptr<{0}>'.format(res)
				return res
			else:
				if type.isconst:
					res += 'const '
				res += CppTranslator.__abstract_base_type_to_cpp(type.type)
				if type.isreference:
					res += ' &'
				return res
		else:
			return 'void'
	
	def translate_class_name(self, name):
		res = ''
		for word in name.words:
			res += word.title()
		return res
	
	def translate_enum_name(self, name):
		return CppTranslator.translate_class_name(self, name)
	
	def translate_enum_value_name(self, name):
		return CppTranslator.translate_class_name(self, name)
	
	def translate_method_name(self, name):
		res = ''
		first = True
		for word in name.words:
			if first:
				first = False
				res += word
			else:
				res += word.title()
		return res
	
	@staticmethod
	def __abstract_base_type_to_cpp(atype):
		if atype == 'boolean':
			return 'bool'
		elif atype == 'character':
			return 'char'
		elif atype == 'integer':
			return 'int'
		elif atype == 'floatant':
			return 'float'
		elif atype == 'string':
			return 'std::string'
		else:
			raise RuntimeError('\'{0}\' is not a base abstlract type'.format(atype))


class EnumsHeader(object):
	def __init__(self, translator):
		self.translator = translator
		self.enums = []
	
	def add_enum(self, enum):
		self.enums.append(enum.translate(translator))


class ClassHeader(object):
	def __init__(self, _class, translator):
		self._class = _class.translate(translator)
		self.define = ClassHeader._class_name_to_define(_class.name)
		self.filename = ClassHeader._class_name_to_filename(_class.name)
		self.internalIncludes = []
		self.exteranlIncludes = []
		self.update_includes(_class)
	
	def update_includes(self, _class):
		internalInc = set()
		externalInc = set()
		for method in _class.classMethods:
			if method.returnType.isobject:
				externalInc.add('memory')
				internalInc.add('_'.join(method.returnType.type.words))
		self.internalIncludes = []
		self.externalIncludes = []
		for include in internalInc:
			self.internalIncludes.append({'name': include})
		for include in externalInc:
			self.externalIncludes.append({'name': include})
	
	@staticmethod
	def _class_name_to_define(className):
		words = className.words
		res = ''
		for word in words:
			res += ('_' + word.upper())
		res += '_HH'
		return res

	@staticmethod
	def _class_name_to_filename(className):
		words = className.words
		res = ''
		first = True
		for word in words:
			if first:
				first = False
			else:
				res += '_'
			res += word.lower()
		
		res += '.hh'
		return res


if __name__ == '__main__':
	project = CApi.Project()
	project.initFromDir('../../work/coreapi/help/doc/xml')
	project.check()
	
	translator = CppTranslator()
	
	header = EnumsHeader(translator)
	
	linphoneNs = AbsApi.Namespace(name='linphone')
	for cEnum in project.enums:
		aEnum = AbsApi.Enum()
		aEnum.set_from_c(cEnum, namespace=linphoneNs)
		header.add_enum(aEnum)
	
	renderer = pystache.Renderer()	
	with open('include/enums.hh', mode='w') as f:
		f.write(renderer.render(header))
	
	for cClass in project.classes:
		try:
			aClass = AbsApi.Class()
			aClass.set_from_c(cClass, namespace=linphoneNs)
			header = ClassHeader(aClass, translator)
			with open('include/' + header.filename, mode='w') as f:
				f.write(renderer.render(header))
		except Exception as e:
			print('Ignoring "{0}". {1}'.format(cClass.name, e.args[0]))
