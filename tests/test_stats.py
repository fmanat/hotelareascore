from hotelareascore.stats import kendall_tau, rank, spearman


def test_rank_no_ties():
    assert rank([10, 30, 20]) == [1, 3, 2]


def test_rank_with_ties_uses_average():
    assert rank([5, 5, 1]) == [2.5, 2.5, 1]


def test_spearman_perfect_positive():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0


def test_spearman_perfect_negative():
    assert spearman([1, 2, 3, 4], [40, 30, 20, 10]) == -1.0


def test_spearman_no_relationship_constant_y():
    # constant y has zero variance -> undefined correlation
    result = spearman([1, 2, 3], [5, 5, 5])
    assert result != result  # nan


def test_spearman_matches_known_reference_value():
    # Reference case (verified against scipy.stats.spearmanr elsewhere):
    # x=[1,2,3,4,5], y=[5,6,7,8,7] -> rho = 0.8207826816681233
    rho = spearman([1, 2, 3, 4, 5], [5, 6, 7, 8, 7])
    assert abs(rho - 0.8207826816681233) < 1e-9


def test_kendall_tau_perfect_agreement():
    assert kendall_tau([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0


def test_kendall_tau_perfect_disagreement():
    assert kendall_tau([1, 2, 3, 4], [40, 30, 20, 10]) == -1.0


def test_kendall_tau_ties_excluded_from_total():
    # one tied pair on x is excluded entirely (tau-a convention)
    tau = kendall_tau([1, 1, 2], [5, 6, 7])
    assert tau == 1.0
