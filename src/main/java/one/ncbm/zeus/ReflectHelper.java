package one.ncbm.zeus;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.GenericArrayType;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.Parameter;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.lang.reflect.TypeVariable;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class ReflectHelper {
    @SuppressWarnings("unused")  // used externally
    public static Map<String, Object> generateClassSignature(Class<?> clazz) {
        Map<String, Object> signature = new LinkedHashMap<>();
        
        // 基础信息
        signature.put("package", clazz.getPackage().getName());
        signature.put("class_name", clazz.getSimpleName());
        
        // 继承关系
        processSuperclass(clazz, signature);
        processInterfaces(clazz, signature);
        
        // 泛型信息
        signature.put("generics", processTypeParameters(clazz.getTypeParameters()));
        
        // 成员信息
        signature.put("methods", processMethods(clazz.getDeclaredMethods()));
        signature.put("fields", processFields(clazz.getDeclaredFields()));
        signature.put("constructors", processConstructors(clazz.getDeclaredConstructors()));
        
        return signature;
    }

    // 处理父类信息
    private static void processSuperclass(Class<?> clazz, Map<String, Object> signature) {
        Type superclass = clazz.getGenericSuperclass();
        if (superclass != null && !superclass.equals(Object.class)) {
            signature.put("extends", typeToString(superclass));
        }
    }

    // 处理接口实现
    private static void processInterfaces(Class<?> clazz, Map<String, Object> signature) {
        Type[] interfaces = clazz.getGenericInterfaces();
        if (interfaces.length > 0) {
            List<String> interfaceNames = new ArrayList<>();
            for (Type interfaceType : interfaces) {
                interfaceNames.add(typeToString(interfaceType));
            }
            signature.put("implements", interfaceNames);
        }
    }

    // 处理方法泛型参数
    private static List<Map<String, Object>> processMethodTypeParameters(TypeVariable<Method>[] typeParams) {
        List<Map<String, Object>> generics = new ArrayList<>();
        for (TypeVariable<Method> tv : typeParams) {
            Map<String, Object> generic = new LinkedHashMap<>();
            generic.put("name", tv.getName());
            
            // 处理泛型约束
            Type[] bounds = tv.getBounds();
            if (bounds.length > 0 && !bounds[0].equals(Object.class)) {
                generic.put("extends", typeToString(bounds[0]));
            }
            
            generics.add(generic);
        }
        return generics;
    }

    // 处理方法
    private static List<Map<String, Object>> processMethods(Method[] methods) {
        List<Map<String, Object>> methodList = new ArrayList<>();
        for (Method m : methods) {
            if (!Modifier.isPublic(m.getModifiers()) && !Modifier.isProtected(m.getModifiers())) {
                continue;
            }
            
            Map<String, Object> method = new LinkedHashMap<>();
            method.put("name", m.getName());
            method.put("return_type", processType(m.getGenericReturnType()));
            method.put("parameters", processParameters(m.getGenericParameterTypes(), 
                                                    m.getParameters(),
                                                    m.isVarArgs()));
            
            // 新增：处理方法级别的泛型参数
            TypeVariable<Method>[] typeParams = m.getTypeParameters();
            if (typeParams.length > 0) {
                method.put("generics", processMethodTypeParameters(typeParams));
            }
            
            // 方法修饰符
            int modifiers = m.getModifiers();
            if (Modifier.isStatic(modifiers)) method.put("static", true);
            if (Modifier.isFinal(modifiers)) method.put("final", true);
            if (Modifier.isProtected(modifiers)) method.put("protected", true);
            
            boolean asOverload = false;
            for (Map<String, Object> meth : methodList) {
                if (meth.get("name").equals(m.getName())) {
                    meth.put("overload", method);
                    asOverload = true;
                    break;
                }
            }

            if (!asOverload) {
                methodList.add(method);
            }
        }
        return methodList;
    }

    // 处理泛型参数
    private static List<Map<String, Object>> processTypeParameters(TypeVariable<?>[] typeParams) {
        List<Map<String, Object>> generics = new ArrayList<>();
        for (TypeVariable<?> tv : typeParams) {
            Map<String, Object> generic = new LinkedHashMap<>();
            generic.put("name", tv.getName());
            
            // 处理泛型约束
            Type[] bounds = tv.getBounds();
            if (bounds.length > 0 && !bounds[0].equals(Object.class)) {
                generic.put("extends", typeToString(bounds[0]));
            }
            
            generics.add(generic);
        }
        return generics;
    }

    // 处理字段
    private static List<Map<String, Object>> processFields(Field[] fields) {
        List<Map<String, Object>> fieldList = new ArrayList<>();
        for (Field f : fields) {
            if (!Modifier.isPublic(f.getModifiers()) && !Modifier.isProtected(f.getModifiers())) {
                continue;
            }
            
            Map<String, Object> field = new LinkedHashMap<>();
            field.put("name", f.getName());
            field.put("type", processType(f.getGenericType()));
            
            // 字段修饰符
            int modifiers = f.getModifiers();
            if (Modifier.isStatic(modifiers)) field.put("static", true);
            if (Modifier.isFinal(modifiers)) field.put("final", true);
            if (Modifier.isProtected(modifiers)) field.put("protected", true);
            
            fieldList.add(field);
        }
        return fieldList;
    }

    // 处理构造器
    private static List<Map<String, Object>> processConstructors(Constructor<?>[] constructors) {
        List<Map<String, Object>> constructorList = new ArrayList<>();
        for (Constructor<?> c : constructors) {
            if (!Modifier.isPublic(c.getModifiers()) && !Modifier.isProtected(c.getModifiers())) {
                continue;
            }
            
            Map<String, Object> constructor = new LinkedHashMap<>();
            constructor.put("parameters", processParameters(
                c.getGenericParameterTypes(),
                c.getParameters(),
                false // 构造器不支持varargs
            ));
            
            if (Modifier.isProtected(c.getModifiers())) {
                constructor.put("protected", true);
            }
            
            constructorList.add(constructor);
        }
        return constructorList;
    }

    // 处理参数列表
    private static List<Map<String, Object>> processParameters(
            Type[] paramTypes, 
            Parameter[] params, 
            boolean isVarArgs) {
        List<Map<String, Object>> paramList = new ArrayList<>();
        for (int i = 0; i < paramTypes.length; i++) {
            Map<String, Object> param = new LinkedHashMap<>();
            param.put("name", params[i].getName());
            
            // 处理可变参数
            Type paramType = paramTypes[i];
            if (isVarArgs && i == paramTypes.length - 1) {
                param.put("vararg", true);
                if (paramType instanceof GenericArrayType) {
                    paramType = ((GenericArrayType) paramType).getGenericComponentType();
                }
            }
            
            param.put("type", processType(paramType));
            paramList.add(param);
        }
        return paramList;
    }

    // 类型处理核心方法
    private static Map<String, Object> processType(Type type) {
        Map<String, Object> typeInfo = new LinkedHashMap<>();

        switch (type) {
            case Class<?> clazz -> {
                typeInfo.put("type", clazz.getCanonicalName());

                // 处理数组维度
                if (clazz.isArray()) {
                    typeInfo.put("dimensions", getArrayDimensions(clazz));
                }
            }
            case ParameterizedType pType -> {
                typeInfo.put("type", ((Class<?>) pType.getRawType()).getCanonicalName());

                // 处理泛型参数
                List<Map<String, Object>> generics = new ArrayList<>();
                for (Type arg : pType.getActualTypeArguments()) {
                    generics.add(processType(arg));
                }
                typeInfo.put("generics", generics);
            }
            case TypeVariable<?> typeVariable -> typeInfo.put("type", typeVariable.getName());
            case GenericArrayType arrayType -> {
                Map<String, Object> componentType = processType(arrayType.getGenericComponentType());
                typeInfo.put("type", componentType.get("type"));
                typeInfo.put("dimensions",
                        (Integer) componentType.getOrDefault("dimensions", 0) + 1);
            }
            case null, default -> typeInfo.put("type", "java.lang.Object");
        }
        
        return typeInfo;
    }

    // 计算数组维度
    private static int getArrayDimensions(Class<?> arrayClass) {
        int dimensions = 0;
        while (arrayClass.isArray()) {
            dimensions++;
            arrayClass = arrayClass.getComponentType();
        }
        return dimensions;
    }

    // 类型转字符串(用于继承和接口)
    private static String typeToString(Type type) {
        if (type instanceof Class) {
            return ((Class<?>) type).getCanonicalName();
        }
        return type.toString(); // 处理泛型类型
    }
}