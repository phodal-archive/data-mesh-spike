#!/bin/bash

# 查看最新的 Data Quality Validation 日志

AIRFLOW_LOGS_DIR="/Users/phodal/repractise/learn-data-mesh/airflow/logs/dag_id=datamesh_mvp_pipeline"

echo "🔍 Finding latest quality check logs..."
echo ""

# 找到最新的运行
LATEST_RUN=$(ls -t "$AIRFLOW_LOGS_DIR" | grep "run_id=" | head -1)

if [ -z "$LATEST_RUN" ]; then
    echo "❌ No DAG runs found"
    exit 1
fi

LOG_FILE="$AIRFLOW_LOGS_DIR/$LATEST_RUN/task_id=validate_data_quality/attempt=1.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Quality check log not found: $LOG_FILE"
    exit 1
fi

echo "📄 Latest run: $LATEST_RUN"
echo "📍 Log file: $LOG_FILE"
echo ""
echo "=" * 80
echo ""

# 提取关键的质量检查输出（去掉 Airflow 的元数据日志）
grep -A 200 "Data Quality Validation Started" "$LOG_FILE" | \
    grep "INFO -" | \
    sed 's/^.*INFO - //' | \
    grep -v "Exporting env vars" | \
    grep -v "Running:" | \
    grep -v "Done. Returned"

echo ""
echo "=" * 80
echo ""
echo "✅ To view full log:"
echo "   cat \"$LOG_FILE\""
echo ""
echo "💡 To run quality check again:"
echo "   Visit http://localhost:8081 and trigger 'datamesh_mvp_pipeline' DAG"

