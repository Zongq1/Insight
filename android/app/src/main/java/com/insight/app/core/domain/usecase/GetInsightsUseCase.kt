package com.insight.app.core.domain.usecase

import com.insight.app.core.data.repository.InsightRepository
import com.insight.app.core.domain.model.Insight
import com.insight.app.core.util.NetworkResult
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class GetInsightsUseCase @Inject constructor(
    private val repository: InsightRepository,
) {
    operator fun invoke(): Flow<List<Insight>> {
        return repository.getInsights()
    }

    suspend fun refreshFromNetwork(): NetworkResult<List<Insight>> {
        return repository.fetchInsights()
    }

    suspend fun deleteInsight(id: String) {
        repository.deleteInsight(id)
    }

    suspend fun getInsightById(id: String): Insight? {
        return repository.getInsightById(id)
    }
}
