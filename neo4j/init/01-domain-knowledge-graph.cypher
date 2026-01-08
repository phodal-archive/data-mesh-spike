// =============================================================================
// Data Mesh Domain Knowledge Graph
// 用于展示概念、领域、数据产品之间的关系
// =============================================================================

// ---------------------------------------------------------------------------
// 1. 创建约束和索引
// ---------------------------------------------------------------------------
CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT domain_name IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT data_product_name IF NOT EXISTS FOR (dp:DataProduct) REQUIRE dp.name IS UNIQUE;
CREATE CONSTRAINT team_name IF NOT EXISTS FOR (t:Team) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT platform_name IF NOT EXISTS FOR (p:Platform) REQUIRE p.name IS UNIQUE;

// ---------------------------------------------------------------------------
// 2. Data Mesh 核心概念节点
// ---------------------------------------------------------------------------
CREATE (dm:Concept {name: 'Data Mesh', description: '去中心化的数据架构范式'})
CREATE (dop:Concept {name: 'Domain Ownership', description: '领域自治，数据归属于业务领域'})
CREATE (dap:Concept {name: 'Data as Product', description: '数据作为产品，关注数据消费者体验'})
CREATE (ssp:Concept {name: 'Self-Serve Platform', description: '自助服务平台，降低数据使用门槛'})
CREATE (fg:Concept {name: 'Federated Governance', description: '联邦治理，平衡自治与标准化'})

// 核心概念之间的关系
CREATE (dm)-[:CONSISTS_OF {order: 1}]->(dop)
CREATE (dm)-[:CONSISTS_OF {order: 2}]->(dap)
CREATE (dm)-[:CONSISTS_OF {order: 3}]->(ssp)
CREATE (dm)-[:CONSISTS_OF {order: 4}]->(fg)

// ---------------------------------------------------------------------------
// 3. 业务领域节点
// ---------------------------------------------------------------------------
CREATE (dc:Domain {
  name: 'Customers Domain',
  name_cn: '客户领域',
  description: '管理客户主数据、客户行为分析',
  bounded_context: 'customer-management',
  owner: 'customer-team'
})

CREATE (do:Domain {
  name: 'Orders Domain',
  name_cn: '订单领域',
  description: '管理订单全生命周期、交易流程',
  bounded_context: 'order-management',
  owner: 'order-team'
})

CREATE (dp:Domain {
  name: 'Products Domain',
  name_cn: '产品领域',
  description: '管理产品目录、库存、定价',
  bounded_context: 'product-catalog',
  owner: 'product-team'
})

CREATE (da:Domain {
  name: 'Analytics Domain',
  name_cn: '分析领域',
  description: '跨域分析、业务洞察、数据产品聚合',
  bounded_context: 'business-analytics',
  owner: 'analytics-team'
})

// 领域与概念的关系
CREATE (dc)-[:IMPLEMENTS]->(dop)
CREATE (do)-[:IMPLEMENTS]->(dop)
CREATE (dp)-[:IMPLEMENTS]->(dop)
CREATE (da)-[:IMPLEMENTS]->(dop)

// ---------------------------------------------------------------------------
// 4. 数据产品节点
// ---------------------------------------------------------------------------
// 客户领域数据产品
CREATE (dp_cust:DataProduct {
  name: 'Customer 360',
  name_cn: '客户360视图',
  description: '客户全景视图，整合客户基本信息与订单历史',
  type: 'consumer-aligned',
  quality_sla: '99.9%',
  freshness: 'near-realtime',
  table_name: 'dp_customer_360'
})

// 分析领域数据产品
CREATE (dp_sales:DataProduct {
  name: 'Product Sales',
  name_cn: '产品销售分析',
  description: '产品销售绩效、收入、订单量分析',
  type: 'aggregate',
  quality_sla: '99.5%',
  freshness: 'daily',
  table_name: 'dp_product_sales'
})

CREATE (dp_kpi:DataProduct {
  name: 'Business KPIs',
  name_cn: '业务KPI',
  description: '核心业务指标，包括收入、订单、客户数',
  type: 'aggregate',
  quality_sla: '99.9%',
  freshness: 'daily',
  table_name: 'dp_business_kpis'
})

// 数据产品与领域的关系
CREATE (dc)-[:OWNS]->(dp_cust)
CREATE (da)-[:OWNS]->(dp_sales)
CREATE (da)-[:OWNS]->(dp_kpi)

// 数据产品之间的依赖关系
CREATE (dp_cust)-[:CONSUMES_FROM]->(dc)
CREATE (dp_cust)-[:CONSUMES_FROM]->(do)
CREATE (dp_sales)-[:CONSUMES_FROM]->(dp)
CREATE (dp_sales)-[:CONSUMES_FROM]->(do)
CREATE (dp_kpi)-[:CONSUMES_FROM]->(dc)
CREATE (dp_kpi)-[:CONSUMES_FROM]->(do)
CREATE (dp_kpi)-[:CONSUMES_FROM]->(dp)

// 数据产品实现 Data as Product 概念
CREATE (dp_cust)-[:IMPLEMENTS]->(dap)
CREATE (dp_sales)-[:IMPLEMENTS]->(dap)
CREATE (dp_kpi)-[:IMPLEMENTS]->(dap)

// ---------------------------------------------------------------------------
// 5. 平台组件节点
// ---------------------------------------------------------------------------
CREATE (trino:Platform {name: 'Trino', role: 'Query Engine', description: '联邦查询引擎，跨域数据访问'})
CREATE (omd:Platform {name: 'OpenMetadata', role: 'Data Catalog', description: '数据目录，元数据管理'})
CREATE (airflow:Platform {name: 'Airflow', role: 'Orchestration', description: '数据编排，Pipeline管理'})
CREATE (backstage:Platform {name: 'Backstage', role: 'Developer Portal', description: '开发者门户，服务目录'})
CREATE (superset:Platform {name: 'Superset', role: 'BI', description: '商业智能，自助报表'})
CREATE (neo4j:Platform {name: 'Neo4j', role: 'Knowledge Graph', description: '知识图谱，概念关系可视化'})

// 平台实现 Self-Serve Platform 概念
CREATE (trino)-[:IMPLEMENTS]->(ssp)
CREATE (omd)-[:IMPLEMENTS]->(ssp)
CREATE (airflow)-[:IMPLEMENTS]->(ssp)
CREATE (backstage)-[:IMPLEMENTS]->(ssp)
CREATE (superset)-[:IMPLEMENTS]->(ssp)
CREATE (neo4j)-[:IMPLEMENTS]->(ssp)

// 平台组件之间的关系
CREATE (superset)-[:CONNECTS_TO]->(trino)
CREATE (trino)-[:QUERIES]->(dc)
CREATE (trino)-[:QUERIES]->(do)
CREATE (trino)-[:QUERIES]->(dp)
CREATE (trino)-[:QUERIES]->(da)
CREATE (omd)-[:CATALOGS]->(dc)
CREATE (omd)-[:CATALOGS]->(do)
CREATE (omd)-[:CATALOGS]->(dp)
CREATE (omd)-[:CATALOGS]->(da)
CREATE (airflow)-[:ORCHESTRATES]->(dp_cust)
CREATE (airflow)-[:ORCHESTRATES]->(dp_sales)
CREATE (airflow)-[:ORCHESTRATES]->(dp_kpi)

// ---------------------------------------------------------------------------
// 6. 团队节点
// ---------------------------------------------------------------------------
CREATE (ct:Team {name: 'Customer Team', name_cn: '客户团队', responsibility: '客户数据产品开发与维护'})
CREATE (ot:Team {name: 'Order Team', name_cn: '订单团队', responsibility: '订单数据产品开发与维护'})
CREATE (pt:Team {name: 'Product Team', name_cn: '产品团队', responsibility: '产品数据产品开发与维护'})
CREATE (at:Team {name: 'Analytics Team', name_cn: '分析团队', responsibility: '分析数据产品与洞察'})
CREATE (plt:Team {name: 'Platform Team', name_cn: '平台团队', responsibility: '数据平台建设与运维'})

// 团队与领域的关系
CREATE (ct)-[:OWNS]->(dc)
CREATE (ot)-[:OWNS]->(do)
CREATE (pt)-[:OWNS]->(dp)
CREATE (at)-[:OWNS]->(da)
CREATE (plt)-[:MAINTAINS]->(trino)
CREATE (plt)-[:MAINTAINS]->(omd)
CREATE (plt)-[:MAINTAINS]->(airflow)
CREATE (plt)-[:MAINTAINS]->(backstage)
CREATE (plt)-[:MAINTAINS]->(superset)
CREATE (plt)-[:MAINTAINS]->(neo4j)

// ---------------------------------------------------------------------------
// 7. 治理概念
// ---------------------------------------------------------------------------
CREATE (dq:Concept {name: 'Data Quality', name_cn: '数据质量', description: '数据准确性、完整性、一致性'})
CREATE (lin:Concept {name: 'Data Lineage', name_cn: '数据血缘', description: '数据流转追踪，端到端可追溯'})
CREATE (sec:Concept {name: 'Data Security', name_cn: '数据安全', description: '数据访问控制、隐私保护'})
CREATE (sla:Concept {name: 'SLA', name_cn: '服务等级协议', description: '数据产品的质量承诺'})

// 治理概念与联邦治理的关系
CREATE (dq)-[:PART_OF]->(fg)
CREATE (lin)-[:PART_OF]->(fg)
CREATE (sec)-[:PART_OF]->(fg)
CREATE (sla)-[:PART_OF]->(fg)

// 平台实现治理概念
CREATE (omd)-[:ENABLES]->(dq)
CREATE (omd)-[:ENABLES]->(lin)
CREATE (airflow)-[:ENABLES]->(dq)

// ---------------------------------------------------------------------------
// 8. 领域之间的业务关系
// ---------------------------------------------------------------------------
CREATE (do)-[:DEPENDS_ON {type: 'customer_reference'}]->(dc)
CREATE (do)-[:DEPENDS_ON {type: 'product_reference'}]->(dp)
CREATE (da)-[:AGGREGATES]->(dc)
CREATE (da)-[:AGGREGATES]->(do)
CREATE (da)-[:AGGREGATES]->(dp)

RETURN 'Domain Knowledge Graph initialized successfully!' AS status;

