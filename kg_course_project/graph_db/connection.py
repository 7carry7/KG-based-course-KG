# Neo4j 驱动连接管理
from neo4j import GraphDatabase
# 查询节点数和关系数的代码

class Neo4jConnection:
    """管理 Neo4j 驱动和会话"""

    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()
    # Community Edition只支持一个数据库，所以database不起作用
    def run_query(self, query, parameters=None, database="neo4j"):
        """运行一个读/写查询并返回结果"""
        with self.driver.session(database=database) as session:
            result = session.run(query, parameters)
            return [record for record in result]
    '''
    # await: 等待异步操作完成
    async def run_query(self, query, parameters=None):
        async with self.driver.session() as session:
            result = await session.run(query, parameters)
            return [record async for record in result]
    '''



    def execute_write(self, query, parameters=None, database="neo4j"):
        """
        在事务中执行写操作 (推荐用于所有写操作)
        """
        with self.driver.session(database=database) as session:
            session.execute_write(self._run_tx, query, parameters)

    @staticmethod
    def _run_tx(tx, query, parameters=None):
        #  事务对象，由驱动自动传入
        tx.run(query, parameters)

if __name__ == '__main__':
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "ChenMoody"
    connection = Neo4jConnection(uri=URI, auth=(USER, PASSWORD))