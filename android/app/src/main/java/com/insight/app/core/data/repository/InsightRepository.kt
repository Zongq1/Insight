package com.insight.app.core.data.repository

import com.insight.app.core.data.local.dao.InsightDao
import com.insight.app.core.data.local.entity.InsightEntity
import com.insight.app.core.data.remote.ApiService
import com.insight.app.core.data.remote.dto.InsightDto
import com.insight.app.core.domain.model.Insight
import com.insight.app.core.domain.model.LogicPoint
import com.insight.app.core.domain.model.Source
import com.insight.app.core.util.NetworkResult
import com.insight.app.core.util.safeApiCall
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InsightRepository @Inject constructor(
    private val insightDao: InsightDao,
    private val apiService: ApiService,
    private val moshi: Moshi,
) {
    fun getInsights(): Flow<List<Insight>> {
        return insightDao.getAllInsights().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    fun getInsightsByCategory(category: String): Flow<List<Insight>> {
        return insightDao.getInsightsByCategory(category).map { entities ->
            entities.map { it.toDomain() }
        }
    }

    suspend fun fetchInsights(): NetworkResult<List<Insight>> {
        return when (val result = safeApiCall { apiService.getAllInsights() }) {
            is NetworkResult.Success -> {
                val insights = result.data.map { it.toDomain() }
                insightDao.insertInsights(insights.map { it.toEntity() })
                NetworkResult.Success(insights)
            }
            is NetworkResult.Error -> result
            is NetworkResult.Loading -> result
        }
    }

    suspend fun deleteInsight(id: String) {
        insightDao.getInsightById(id)?.let { entity ->
            insightDao.deleteInsight(entity)
        }
    }

    suspend fun getInsightById(id: String): Insight? {
        return insightDao.getInsightById(id)?.toDomain()
    }

    private fun InsightEntity.toDomain(): Insight {
        val logicChainType = Types.newParameterizedType(List::class.java, LogicPoint::class.java)
        val logicChainAdapter = moshi.adapter<List<LogicPoint>>(logicChainType)
        val sourcesType = Types.newParameterizedType(List::class.java, Source::class.java)
        val sourcesAdapter = moshi.adapter<List<Source>>(sourcesType)

        return Insight(
            id = id,
            category = category,
            coreThesis = coreThesis,
            logicChain = logicChainAdapter.fromJson(logicChainJson) ?: emptyList(),
            sources = sourcesAdapter.fromJson(sourcesJson) ?: emptyList(),
            confidenceScore = confidenceScore,
            historicalInsight = historicalInsight,
            dateGenerated = "",
        )
    }

    private fun Insight.toEntity(): InsightEntity {
        val logicChainType = Types.newParameterizedType(List::class.java, LogicPoint::class.java)
        val logicChainAdapter = moshi.adapter<List<LogicPoint>>(logicChainType)
        val sourcesType = Types.newParameterizedType(List::class.java, Source::class.java)
        val sourcesAdapter = moshi.adapter<List<Source>>(sourcesType)

        return InsightEntity(
            id = id,
            category = category,
            coreThesis = coreThesis,
            logicChainJson = logicChainAdapter.toJson(logicChain) ?: "[]",
            sourcesJson = sourcesAdapter.toJson(sources) ?: "[]",
            confidenceScore = confidenceScore,
            historicalInsight = historicalInsight,
        )
    }

    private fun InsightDto.toDomain() = Insight(
        id = id,
        category = category,
        coreThesis = core_thesis,
        logicChain = logic_chain.map { LogicPoint(it.premise, it.conclusion) },
        sources = sources.map { Source(it.name, it.url) },
        confidenceScore = confidence_score,
        historicalInsight = historical_insight,
        dateGenerated = date_generated,
    )
}
