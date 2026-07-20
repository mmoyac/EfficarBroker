import { useQuery } from "@tanstack/react-query";
import { getNavigationMenu } from "@/services/auth";

export function useNavigationMenu() {
  return useQuery({
    queryKey: ["navigation-menu"],
    queryFn: getNavigationMenu,
  });
}
