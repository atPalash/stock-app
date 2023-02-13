class RetVal:
    def __init__(self, obj, obj_as_str="", errors="") -> None:
        """Return object type for systems module

        Args:
            obj (_type_): object 
            obj_as_str (str, optional): string representation or string information about object type
            errors (str, optional): errors encountered
        """
        self.obj = obj
        self.obj_as_string = ""
        if obj_as_str == "":
            self.obj_as_string = str(obj)
        else:
            self.obj_as_string = obj_as_str
        self.errors = errors

class SystemIf:
    def execute(self) -> RetVal:
        """Api to call the system and execute

        Returns:
            RetVal: return object
        """
        pass

    def __get() -> RetVal:
        """Primary method implemented by all systems. To be called via execute.

        Returns:
            RetVal: return object
        """
        pass