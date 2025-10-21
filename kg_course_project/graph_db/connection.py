# Neo4j 驱动连接管理
from neo4j import GraphDatabase


class Neo4jConnection:
    """管理 Neo4j 驱动和会话"""

    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None, database="neo4j"):
        """运行一个读/写查询并返回结果"""
        with self.driver.session(database=database) as session:
            result = session.run(query, parameters)
            return [record for record in result]
    '''
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