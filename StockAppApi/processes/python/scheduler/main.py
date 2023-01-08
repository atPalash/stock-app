from StockAppApi.processes.python.scheduler.src.system import SystemScheduler
from StockAppApi.processes.python.scheduler.src.yahoofinance import YahooScheduler
from StockAppApi.processes.python.scheduler.src.command_handler import CommandHandler
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.base.python.src.server import Server

if __name__ == "__main__":
        print("Hello Scheduler!")
        
        configFolder = "StockAppApi/configuration/"
        config = read_config(configFolder + "config.yaml")
        serverPort = config['port']['scheduler']
        masterServerPort = config['port']['master']
        
        indicator_config_yaml = configFolder + "indicator.yaml"   
        selected_stocks_yaml = configFolder + "selected_stocks.yaml"
        
        system_scheduler = SystemScheduler(indicator_config_file=indicator_config_yaml, 
                                        selected_stocks_config_file=selected_stocks_yaml, 
                                        master_url=f"http://localhost:{masterServerPort}")
        yahoo_scheduler = YahooScheduler(indicator_config_file=indicator_config_yaml, 
                                        selected_stocks_config_file=selected_stocks_yaml, 
                                        master_url=f"http://localhost:{masterServerPort}")
        system_scheduler.run()
        yahoo_scheduler.run()

        command_handler = CommandHandler(system_scheduler=system_scheduler, yahoo_scheduler=yahoo_scheduler)
        
        server = Server(serverPort, masterServerPort, command_handler)
        server.register_routes()
        server.run()
        server.unregister_routes()
