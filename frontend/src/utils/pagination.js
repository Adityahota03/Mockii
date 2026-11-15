export const getPaginatedData = (data, pageSize) => {
  const results = Array.isArray(data?.results)
    ? data.results
    : [];

  const count = Number(data?.count) || 0;

  const safePageSize = Number(pageSize) > 0 ? Number(pageSize) : 10;

  const totalPages = Math.max(
    1,
    Math.ceil(count / safePageSize)
  );

  return {
    results,
    count,
    totalPages,
    next: data?.next || null,
    previous: data?.previous || null,
  };
};
