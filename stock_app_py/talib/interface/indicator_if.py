from abc import abstractmethod

class IndicatorIf:
    """
    This is the interface class which is implemented by the indicators.
    """          
    @abstractmethod 
    def execute_command(self, command:str, condition="")->dict:
        """Get the result of query

        Args:
            command (str): sub command which will be executed.
            condition (str, optional): to validate. Defaults to "".

        Returns:
            dict: staus with result of analysis
        """
        pass 
    
    @abstractmethod
    def _do_analysis(self):
        """Read the OHLC data from the csv, append the dataframe with latest data
        and perform analysis
        """
        pass

    @abstractmethod
    def _result(self, status:bool, obj: object) -> dict:
        pass
